# @Author  : sudoskys
import itertools
import json
import logging
from typing import Union

import curl_cffi
from curl_cffi.requests import AsyncSession
from pydantic import ConfigDict, Field, PrivateAttr, field_validator, model_validator

from novelai_python._retry import retry_on_server_error

from ...._enum import (
    COLORS_LLM,
    TextLLMModel,
    TextLLMModelTypeAlias,
    TextTokenizerGroup,
    as_text_model,
    get_llm_group,
    get_token_dtype,
    get_tokenizer_model,
)
from ...._exceptions import APIError, SessionHttpError
from ...._response.ai.generate import LLMResp
from ....credential import CredentialBase
from ....metrics import get_metrics
from ....tokenizer import get_tokenizer
from ....utils import try_jsonfy
from ....utils.encode import tokens_to_b64
from ...schema import ApiBaseModel, use_session
from ._enum import (
    get_bad_words_ids,
    get_default_preset,
    get_eos_token_id,
    get_logit_bias_group,
    get_repetition_penalty_whitelist,
    pickup_reverse_bias_model,
)
from ._enum import (
    get_end_exclude_sequences as get_end_exclude_sequences,
)
from ._schema import AdvanceLLMSetting, Key, KeyOrderEntry, LLMGenerationParams, LogitBiasGroup, PenStyle

logger = logging.getLogger(__name__)


class LLM(ApiBaseModel):
    """
    LLM for /ai/generate
    """

    _endpoint: str = PrivateAttr("https://text.novelai.net")
    input: str = Field(..., description="Base64 encoded token text")
    model: TextLLMModelTypeAlias = TextLLMModel.ERATO
    """Model to use"""

    advanced_setting: AdvanceLLMSetting = AdvanceLLMSetting()
    """Advanced Setting"""

    parameters: LLMGenerationParams | None = None
    """Optional: Generation Parameters"""

    default_bias: bool | None = True
    """Default Bias"""

    logprobs_count: int | None = None
    """Logprobs Count"""

    bias_dinkus_asterism: bool | None = False
    prefix: str | None = "vanilla"
    model_config = ConfigDict(extra="ignore")

    @property
    def base_url(self) -> str:
        return f"{self.endpoint.strip('/')}/ai/generate"

    @field_validator("model", mode="after")
    @classmethod
    def _model_enum(cls, value: TextLLMModelTypeAlias) -> TextLLMModelTypeAlias:
        # A JSON body brings the model as a string; the checks below compare with TextLLMModel
        return as_text_model(value)

    @model_validator(mode="after")
    def normalize_model(self):
        # The validator rewrites both in place: never touch a caller's object or a cached preset
        self.advanced_setting = self.advanced_setting.model_copy(deep=True)
        if self.parameters is not None:
            self.parameters = self.parameters.model_copy(deep=True)
        if self.model in [
            TextLLMModel.NEO_2B,
            TextLLMModel.J_6B,
            TextLLMModel.J_6B_V3,
            TextLLMModel.J_6B_V4,
            TextLLMModel.GENJI_JP_6B,
            TextLLMModel.GENJI_JP_6B_V2,
            TextLLMModel.GENJI_PYTHON_6B,
            TextLLMModel.EUTERPE_V0,
            TextLLMModel.EUTERPE_V2,
            TextLLMModel.KRAKE_V1,
            TextLLMModel.KRAKE_V2,
            TextLLMModel.CASSANDRA,
            TextLLMModel.COMMENT_BOT,
            TextLLMModel.INFILL,
            TextLLMModel.CLIO,
        ]:
            self.endpoint = "https://api.novelai.net"
        tokenizer = get_tokenizer(get_tokenizer_model(self.model))
        model_group = get_llm_group(self.model)
        total_tokens = tokenizer.total_tokens()
        if isinstance(self.input, str):
            prompt = tokenizer.encode(self.input)
            self.input = tokens_to_b64(prompt, dtype=get_token_dtype(self.model))
        if not self.parameters:
            self.parameters = get_default_preset(self.model).parameters.model_copy(deep=True)

        # repetition_penalty_default_whitelist
        if self.parameters.repetition_penalty_default_whitelist and self.model in [
            TextLLMModel.CLIO,
            TextLLMModel.KAYRA,
            TextLLMModel.ERATO,
            *COLORS_LLM,
        ]:
            if not isinstance(self.parameters.repetition_penalty_whitelist, list):
                self.parameters.repetition_penalty_whitelist = []
            self.parameters.repetition_penalty_whitelist += list(
                itertools.chain.from_iterable(
                    [tokenizer.encode(tok) for tok in get_repetition_penalty_whitelist(model_group)]
                )
            )
            self.parameters.repetition_penalty_default_whitelist = None

        # bad_words_ids
        bad_words_ids = [[16067]] if self.model == TextLLMModel.ERATO else []
        if self.advanced_setting.bracket_ban:
            bad_words_ids = bad_words_ids + get_bad_words_ids(model_group, use_banBrackets=True)
        if self.bias_dinkus_asterism:
            bad_words_ids = bad_words_ids + get_bad_words_ids(model_group, use_banBrackets=False)
            if self.model in [TextLLMModel.CLIO, TextLLMModel.KAYRA, TextLLMModel.ERATO, *COLORS_LLM]:
                self.parameters.eos_token_id = get_eos_token_id(model_group)
                if (self.parameters.min_length or 0) < 5:
                    self.parameters.min_length = 5
                """
                endExcludeSequences = get_end_exclude_sequences(model_group)
                """
                # context.length < 30
                if len(self.input) < 3000:
                    bad_words_ids = [*bad_words_ids, [self.parameters.eos_token_id]]

        # 有效的 logit_bias_group_exp
        self.parameters.logit_bias_groups = get_logit_bias_group(model_group)
        logit_bias_group_exp = []
        if self.default_bias:
            bias = -0.12
            sequence_list = []
            if self.model not in [TextLLMModel.NEO_2B, TextLLMModel.INFILL]:
                if model_group in [TextTokenizerGroup.GPT2]:
                    sequence_list = [[8162], [46256, 224]]
                elif model_group in [TextTokenizerGroup.PILE]:
                    sequence_list = [[9264]]
                elif model_group in [TextTokenizerGroup.PILE_NAI]:
                    sequence_list = [[9264], [50260]]
                elif model_group in [TextTokenizerGroup.NERDSTASH, TextTokenizerGroup.NERDSTASH_V2]:
                    sequence_list = [[23], [21]]
                    bias = -0.08
            for sequence in sequence_list:
                # 如果不重复
                if not any(cell.sequence == sequence and cell.bias == bias for cell in logit_bias_group_exp):
                    logit_bias_group_exp.append(
                        LogitBiasGroup(sequence=sequence, bias=bias, ensure_sequence_finish=False, generate_once=False)
                    )
        if (
            self.model
            in [
                TextLLMModel.J_6B,
                TextLLMModel.J_6B_V4,
                TextLLMModel.J_6B_V3,
                TextLLMModel.J_6B_V4,
                TextLLMModel.EUTERPE_V0,
                TextLLMModel.EUTERPE_V2,
                TextLLMModel.GENJI_PYTHON_6B,
                TextLLMModel.GENJI_JP_6B,
                TextLLMModel.GENJI_JP_6B_V2,
            ]
            and self.parameters.repetition_penalty is not None
        ):
            self.parameters.repetition_penalty = (self.parameters.repetition_penalty - 1) * -0.5249999999999999 / -7 + 1
        if self.prefix == "" or self.model in [
            TextLLMModel.J_6B,
            TextLLMModel.J_6B_V3,
            TextLLMModel.J_6B_V4,
            TextLLMModel.EUTERPE_V0,
            TextLLMModel.EUTERPE_V2,
            TextLLMModel.KRAKE_V1,
            TextLLMModel.KRAKE_V2,
            TextLLMModel.CLIO,
            TextLLMModel.KAYRA,
            *COLORS_LLM,
        ]:
            self.prefix = "vanilla"
        if pickup_reverse_bias_model(self.model) == TextLLMModel.GENJI_JP_6B_V2:
            # 反转 logit_bias_group_exp 的 bias
            for group in logit_bias_group_exp:
                if group.bias is not None:
                    group.bias = -group.bias
        order_queue = []
        for order in self.parameters.order:
            if isinstance(order, KeyOrderEntry):
                if order.enabled:
                    if order.id[0] == Key.TopG[0]:
                        self.parameters.top_g = None
                    order_queue.append(order.id[1])
                else:
                    if order.id[0] == Key.Temperature[0]:
                        self.parameters.temperature = None
                    elif order.id[0] == Key.TopK[0]:
                        self.parameters.top_k = None
                    elif order.id[0] == Key.TopP[0]:
                        self.parameters.top_p = None
                    elif order.id[0] == Key.TFS[0]:
                        self.parameters.tail_free_sampling = None
                    elif order.id[0] == Key.TopA[0]:
                        self.parameters.top_a = None
                    elif order.id[0] == Key.TypicalP[0]:
                        self.parameters.typical_p = None
                    elif order.id[0] == Key.Cfg[0]:
                        self.parameters.cfg_scale = None
                        self.parameters.cfg_uc = None
                    elif order.id[0] == Key.TopG[0]:
                        self.parameters.top_g = None
                    elif order.id[0] == Key.Mirostat[0]:
                        self.parameters.mirostat_tau = None
                        self.parameters.mirostat_lr = None
                    elif order.id[0] == Key.Math1[0]:
                        self.parameters.math1_temp = None
                        self.parameters.math1_quad = None
                        self.parameters.math1_quad_entropy_scale = None
                    elif order.id[0] == Key.MinP[0]:
                        self.parameters.min_p = None
        if self.model not in [TextLLMModel.CLIO, TextLLMModel.KAYRA, *COLORS_LLM]:
            self.parameters.top_g = None
            if Key.TopG[1] in order_queue:
                order_queue.remove(Key.TopG[1])
        if self.model not in [TextLLMModel.CLIO, TextLLMModel.KAYRA, TextLLMModel.ERATO, *COLORS_LLM]:
            self.parameters.mirostat_tau = None
            self.parameters.mirostat_lr = None
            if Key.Mirostat[1] in order_queue:
                order_queue.remove(Key.Mirostat[1])
        if self.model not in [TextLLMModel.KAYRA, TextLLMModel.ERATO, *COLORS_LLM]:
            self.parameters.math1_temp = None
            self.parameters.math1_quad = None
            self.parameters.math1_quad_entropy_scale = None
            if Key.Math1[1] in order_queue:
                order_queue.remove(Key.Math1[1])
        if self.model not in [TextLLMModel.KAYRA, TextLLMModel.ERATO, *COLORS_LLM]:
            self.parameters.min_p = None
            if Key.MinP[1] in order_queue:
                order_queue.remove(Key.MinP[1])
        self.parameters.order = order_queue
        for order in self.parameters.order:
            if isinstance(order, KeyOrderEntry):
                raise ValueError(f"type:KeyOrderEntry list not fully converted into type:int: {order}")

        valid_sequences = []
        for cell in logit_bias_group_exp:
            if any(token < 0 or token >= total_tokens for token in cell.sequence):
                # 超出范围的 Token
                logger.debug(f"Bias [{cell}] contains tokens that are out of range and will be ignored.")
            else:
                # 将有效偏置组添加到列表
                valid_sequences.append(cell)
        if len(valid_sequences) == 0:
            self.advanced_setting.logit_bias_exp = None
        else:
            self.advanced_setting.logit_bias_exp = valid_sequences

        # Prefix
        if self.prefix == "special_pedia":
            bad_words_ids += [[24, 24], [24, 85, 24], [24, 1629], [24, 49287], [24, 49255]]

        valid_bad_words_ids = []
        self.parameters.bad_words_ids = bad_words_ids
        for ban_word in self.parameters.bad_words_ids:
            if any(token < 0 or token >= total_tokens for token in ban_word):
                logger.debug(f"Bad word {ban_word} contains tokens that are out of range and will be ignored.")
            else:
                valid_bad_words_ids.append(ban_word)
        if len(valid_bad_words_ids) > 0:
            self.parameters.bad_words_ids = valid_bad_words_ids
        else:
            self.parameters.bad_words_ids = None

        # Set
        if not self.parameters.logit_bias_groups:
            self.parameters.logit_bias_groups = None
        self.advanced_setting.prefix = self.prefix
        self.advanced_setting.order = order_queue
        self.advanced_setting.num_logprobs = self.logprobs_count
        if not self.advanced_setting.max_length:
            self.advanced_setting.max_length = 40
        if self.parameters.repetition_penalty_range == 0:
            self.parameters.repetition_penalty_range = None
        if self.parameters.repetition_penalty_slope == 0:
            self.parameters.repetition_penalty_slope = None
        return self

    @classmethod
    def build(
        cls,
        prompt: str,
        model: TextLLMModelTypeAlias = TextLLMModel.ERATO,
        phrase_rep_pen: PenStyle = PenStyle.Off,
        *,
        advanced_setting: AdvanceLLMSetting = AdvanceLLMSetting(),
        parameters: LLMGenerationParams | None = None,
        default_bias: bool | None = True,
        logprobs_count: int | None = None,
        bias_dinkus_asterism: bool | None = False,
        prefix: str | None = "vanilla",
        **kwargs,
    ) -> "LLM":
        """
        Generate
        :param phrase_rep_pen: Phrase_rep_pen
        :param prompt: prompt, exp "Hello, World!"
        :param model: TextLLMModelTypeAlias
        :param advanced_setting: AdvanceLLMSetting, default None means auto-select
        :param parameters: LLMGenerationParams, default None means auto-select, use get_model_preset
        :param default_bias: bool, default True
        :param logprobs_count: int, default None
        :param bias_dinkus_asterism: bool, default False
        :param prefix: str, default "vanilla"
        """
        assert isinstance(prompt, str), "Prompt must be a string"
        created = cls(
            input=prompt,
            model=model,
            advanced_setting=advanced_setting,
            parameters=parameters,
            default_bias=default_bias,
            logprobs_count=logprobs_count,
            bias_dinkus_asterism=bias_dinkus_asterism,
            prefix=prefix,
        )
        return created

    @retry_on_server_error()
    async def request(
        self, session: Union[AsyncSession, "CredentialBase"], *, override_headers: dict | None = None
    ) -> LLMResp:
        """
        Generate text using NovelAI's large language models. According to our Terms of Service, all generation requests must be initiated by a human action. Automating text or image generation to create excessive load on our systems is not allowed.

        :param override_headers:
        :param session:  session
        :return: LLMStreamResp
        """
        # Data Build
        if self.parameters is None:
            raise ValueError("parameters are not set")
        base_map = self.parameters.get_base_map()
        parameters = {
            **base_map,
            **self.advanced_setting.model_dump(mode="json", exclude_none=True),
        }
        parameters.update(self.parameters.model_dump(mode="json", exclude_none=True).items())
        # Override
        request_data = {
            **self.model_dump(mode="json", include={"input", "model"}),
            "parameters": parameters,
        }
        async with get_metrics().observe(self.base_url, self.model) as observed, use_session(session) as sess:
            # Header
            if override_headers:
                sess.headers.clear()
                sess.headers.update(override_headers)
            # Log
            logger.debug(f"LLM request data: {json.dumps(request_data)}")
            # Request
            try:
                response = await sess.post(self.base_url, json=request_data, stream=False)
                (observed.ok if response.status_code < 400 else observed.failed)(response.status_code)
                response_data = try_jsonfy(response.content, default_when_error={})
                if not isinstance(response_data, dict):
                    response_data = {}
                message = (
                    response_data.get("error")
                    or response_data.get("message")
                    or f"Server error with status_code {response.status_code}"
                )
                status_code = response_data.get("statusCode", response.status_code)
                if status_code == 200 or status_code == 201:
                    output = response_data.get("output")
                    if not output:
                        raise APIError(
                            f"No Content Returned because {message}",
                            request=request_data,
                            code=response.status_code,
                            response=response.content,
                        )
                    return LLMResp(output=output, text=LLMResp.decode_token(model=self.model, token_str=output))
                elif status_code == 400:
                    raise APIError(
                        f"A validation error occured. {message}",
                        request=request_data,
                        code=status_code,
                        response=message,
                    )
                elif status_code == 401:
                    raise APIError(
                        f"Access Token is incorrect. {message}",
                        request=request_data,
                        code=status_code,
                        response=message,
                    )
                elif status_code == 402:
                    raise APIError(
                        f"An active subscription is required to access this endpoint. {message}",
                        request=request_data,
                        code=status_code,
                        response=message,
                    )
                elif status_code == 409:
                    raise APIError(
                        f"A conflict error occured. {message}", request=request_data, code=status_code, response=message
                    )
                else:
                    raise APIError(
                        f"An unknown error occured. {response.status_code} {message}",
                        request=request_data,
                        code=status_code,
                        response=message,
                    )
            except curl_cffi.requests.errors.RequestsError as exc:
                logger.exception(exc)
                raise SessionHttpError(
                    "An AsyncSession RequestsError occurred, perhaps it's an SSL error. Please try again later!"
                ) from exc
            except APIError:
                raise  # not an unexpected error: keep it out of the handler below
            except Exception as e:
                logger.exception("An unexpected error occurred")
                raise e
