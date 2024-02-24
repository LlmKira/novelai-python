import random
from typing import List

from .tag import (
    cameraPerspective, cameraFocus, backgroundTheme, backgroundColor, cameraAngle, artStyle,
    animalFeatures,
    sinkColor, eyeCharacteristics, eyesExpression, hairLength, backHairStyle, hairFeatures, breastsSize,
    bodyFeatures,
    headWears, clothesAccessories, years, uppers,
    backgroundObjects,
    accessories,
    effects, eyeColors, athletic as bodysuit, hairColors, hairColorExtra, hatOrnaments, uniform, swimsuits, legwear,
    socks,
    action, expression, footwears, bottoms, color as colors
)
from .tag_character import rankMoods, rankCharacter, rankIdentity
from .tag_nsfw import nsfw


class RandomPromptGenerator(object):
    def __init__(self, nsfw_enabled):
        self.nsfw_enabled = nsfw_enabled

    @staticmethod
    def get_weighted_choice(tags, existing_tags: List[str]):
        """
        Get a weighted choice from a list of tags
        :param tags:  a list of tags
        :param existing_tags:  a list of existing tags
        :return:  a tag
        """
        valid_tags = [
            tag
            for tag in tags
            if len(tag) < 3 or not tag[2] or any(sub_tag in existing_tags for sub_tag in tag[2])
        ]
        total_weight = sum(tagr[1] for tagr in valid_tags if len(tagr) > 1)
        if total_weight == 0:
            if isinstance(tags, list):
                rd = random.choice(tags)
            elif isinstance(tags, str):
                rd = tags
            else:
                raise ValueError('get_weighted_choice: should not reach here')
            return rd
        random_number = random.randint(1, total_weight)
        cumulative_weight = 0
        for tag in valid_tags:
            cumulative_weight += tag[1]
            if random_number <= cumulative_weight:
                if isinstance(tag, str):
                    raise Exception("tag is string")
                return tag[0]
        raise ValueError('get_weighted_choice: should not reach here')

    def character_features(self, gender, camera_angle, nsfw_enabled, num_characters, enable_skin_color=True):
        """
        Add character features to the prompt
        :param enable_skin_color:  enable skin
        :param gender:  'm', 'f', 'o'
        :param camera_angle:  the camera angle of the prompt
        :param nsfw_enabled:  True or False
        :param num_characters:  the num of characters in the prompt
        :return:  a list of character features
        """

        features = []
        if random.random() < 0.1:
            features.append(self.get_weighted_choice(animalFeatures, features))
        unique_features = {'mermaid', 'centaur', 'lamia'}
        has_unique_feature = any(feature in features for feature in unique_features)
        if random.random() < 0.1 and enable_skin_color:
            features.append(self.get_weighted_choice(sinkColor, features))
        if random.random() < 0.7:
            features.append(self.get_weighted_choice(eyeColors, features))
        if random.random() < 0.1:
            features.append(self.get_weighted_choice(eyeCharacteristics, features))
        if random.random() < 0.6:
            features.append(self.get_weighted_choice(eyesExpression, features))
        if random.random() < 0.2:
            features.append(self.get_weighted_choice(hairLength, features))
        if random.random() < 0.2:
            features.append(self.get_weighted_choice(backHairStyle, features))
        if random.random() < 0.1:
            features.append(self.get_weighted_choice(hairColors, features))
        if random.random() < 0.1:
            features.append(self.get_weighted_choice(hairColorExtra, features))
            features.append(self.get_weighted_choice(hairColors, features))
        if random.random() < 0.12:
            features.append(self.get_weighted_choice(hairFeatures, features))
        if gender.startswith('f') and random.random() < 0.8:
            features.append(self.get_weighted_choice(breastsSize, features))
        num_body_features = 0
        if num_characters == 1:
            num_body_features = self.get_weighted_choice([[0, 10], [1, 30], [2, 15], [3, 5]], features)
        elif num_characters == 2:
            num_body_features = self.get_weighted_choice([[0, 20], [1, 40], [2, 10]], features)
        else:
            num_body_features = self.get_weighted_choice([[0, 30], [1, 30]], features)
        for _ in range(num_body_features):
            features.append(self.get_weighted_choice(bodyFeatures, features))
        if random.random() < 0.3:
            features.append(self.get_weighted_choice(headWears, features))
            if random.random() < 0.5:
                features.append(self.get_weighted_choice(hatOrnaments, features))
        clothing_type = self.get_weighted_choice(['uniform', 'swimsuit', 'bodysuit', 'normal clothes'], features)
        if nsfw_enabled and random.random() < 0.9:
            undressing_choice = self.get_weighted_choice(nsfw["undressing"], features)
            if undressing_choice:
                features.append(undressing_choice)
            else:
                underwear_choice = self.get_weighted_choice(nsfw["underwear"], features)
                features.append(underwear_choice)
                if random.random() < 0.5:
                    clothing_type = None
            if random.random() < 0.5:
                features.append(self.get_weighted_choice(nsfw["naked"], features))
                clothing_type = None
        if clothing_type == 'uniform':
            features.append(self.get_weighted_choice(uniform, features))
        elif clothing_type == 'swimsuit':
            features.append(self.get_weighted_choice(swimsuits, features))
        elif clothing_type == 'bodysuit':
            features.append(self.get_weighted_choice(bodysuit, features))
        elif clothing_type == 'normal clothes':
            if gender.startswith('f') and random.random() < 0.5:
                features.append(self.get_weighted_choice(socks, features))
                if random.random() < 0.3:
                    features.append(self.get_weighted_choice(legwear, features))
            if random.random() < 0.75:
                color = self.get_weighted_choice(colors, features)
                upper_clothing = self.get_weighted_choice(uppers, features)
                features.append(f'{color} {upper_clothing}')
            if not has_unique_feature:
                if random.random() < 0.85:
                    color = self.get_weighted_choice(colors, features)
                    bottom_clothing = self.get_weighted_choice(bottoms, features)
                    features.append(f'{color} {bottom_clothing}')
                if random.random() < 0.7:
                    color = self.get_weighted_choice(colors, features)
                    footwear = self.get_weighted_choice(footwears, features)
                    features.append(f'{color} {footwear}')
        if random.random() < 0.7:
            features.append(self.get_weighted_choice(expression, features))
        if random.random() < (1 if nsfw_enabled and num_characters >= 1 else 0.5):
            # 单角色 + nsfw 为 1
            possible_actions = action
            if nsfw_enabled:
                if random.random() < 0.5:
                    features.append(self.get_weighted_choice(nsfw["action"], features))
                if random.random() < 0.5:
                    features.append(self.get_weighted_choice(nsfw["pussyForeplay"], features))
                possible_actions += nsfw["action"] + nsfw["analForeplay"] + nsfw["pussyForeplay"]
                if random.random() < 0.5:
                    possible_actions += nsfw["footForeplay"]
            features.append(self.get_weighted_choice(possible_actions, features))
        # 睡眠
        if any('sleeping' in feature for feature in features) \
                or any('zzz' in feature for feature in features) \
                or any('closed eyes' in feature for feature in features):
            features = [feature for feature in features if not any(color[0] == feature for color in eyeColors)]
        # 衣物
        num_clothing_accessories = 0
        if num_characters == 1:
            num_clothing_accessories = self.get_weighted_choice([[0, 10], [1, 30], [2, 15], [3, 5]], features)
        elif num_characters == 2:
            num_clothing_accessories = self.get_weighted_choice([[0, 20], [1, 40], [2, 10]], features)
        else:
            num_clothing_accessories = self.get_weighted_choice([[0, 30], [1, 30]], features)
        for _ in range(num_clothing_accessories):
            features.append(
                self.get_weighted_choice(clothesAccessories + (nsfw["nudeExtra"] if nsfw_enabled else []), features))
        if has_unique_feature:
            features = [feature for feature in features if 'legwear' not in feature]
        return features

    def generate(self,
                 *,
                 enable_moods: bool = True,
                 enable_character: bool = False,
                 enable_identity: bool = True,
                 ):
        """
        Generate a random prompt
        :param enable_moods:  enable moods
        :param enable_character:  enable character
        :param enable_identity:  enable identity
        :return:
        """
        return self.random_prompt(
            enable_moods=enable_moods,
            enable_character=enable_character,
            enable_identity=enable_identity
        )

    def random_prompt(self, *,
                      man_w: int = 30,
                      woman_w: int = 60,
                      other_w: int = 10,
                      enable_moods: bool = True,
                      enable_character: bool = True,
                      enable_identity: bool = False,
                      must_appear=None,
                      ):
        if must_appear is None:
            must_appear = []
        tags = []
        # 必须出现的标签
        tags.extend(must_appear)
        if self.nsfw_enabled:
            tags.append('nsfw')
            if random.random() < 0.1:
                tags.append('explicit')
                tags.append('lewd')
        irs = self.get_weighted_choice([[1, 70], [2, 20], [3, 7], [0, 5]], tags)
        if self.nsfw_enabled:
            irs = self.get_weighted_choice([[1, 40], [2, 20], [3, 7]], tags)
        if irs == 0:
            tags.append('no humans')
            if random.random() < 0.3:
                tags.append(self.get_weighted_choice(artStyle, tags))
            tags.append(self.get_weighted_choice(backgroundTheme, tags))
            num_objects = self.get_weighted_choice([[2, 15], [3, 50], [4, 15], [5, 5]], tags)
            for _ in range(num_objects):
                tags.append(self.get_weighted_choice(backgroundObjects, tags))
            num_accessories = self.get_weighted_choice([[0, 15], [1, 10], [2, 20], [3, 20], [4, 20], [5, 15]], tags)
            if (num_accessories - irs) < 0:
                num_accessories = 0
            for _ in range(num_accessories):
                tags.append(self.get_weighted_choice(accessories, tags))
            return ', '.join(tags)
        if random.random() < 0.3:
            tags.append(self.get_weighted_choice(artStyle, tags))
        c_count = 0
        d_count = 0
        u_count = 0
        for _ in range(irs):
            random_gender = self.get_weighted_choice([['m', man_w], ['f', woman_w], ['o', other_w]], tags)
            if random_gender == 'm':
                d_count += 1
            elif random_gender == 'f':
                c_count += 1
            elif random_gender == 'o':
                u_count += 1
        if c_count == 1:
            tags.insert(0, '1girl')
        elif c_count == 2:
            tags.insert(0, '2girls')
        elif c_count == 3:
            tags.insert(0, '3girls')
        if d_count == 1:
            tags.insert(0, '1boy')
        elif d_count == 2:
            tags.insert(0, '2boys')
        elif d_count == 3:
            tags.insert(0, '3boys')
        if u_count == 1:
            tags.insert(0, '1other')
        elif u_count == 2:
            tags.insert(0, '2others')
        elif u_count == 3:
            tags.insert(0, '3others')
        if self.nsfw_enabled:
            g_count = c_count + u_count
            if (c_count >= 2 and d_count == 0) and random.random() < 0.7:
                # 2girls
                tags.append(self.get_weighted_choice(nsfw["yu"], tags))
            if g_count == 0 and d_count >= 2 and c_count == 0:
                tags.append(nsfw["ya"])
            if d_count > 0:
                if c_count > 0:
                    if random.random() < 0.3:
                        tags.append(self.get_weighted_choice(nsfw["penis"], tags))
                else:
                    if random.random() < 0.3:
                        tags.append(self.get_weighted_choice(nsfw["penis"], tags))
            if d_count > 0 and g_count > 0:
                if random.random() < 0.7:
                    tags.append(self.get_weighted_choice(nsfw["analSex"], tags))
            if g_count > 0:
                features = []
                if random.random() < 0.2:
                    features = self.character_features(nsfw['fu'], None, True, irs)
                if random.random() < 0.3:
                    tags.append(self.get_weighted_choice(nsfw["sex"], tags))
                if random.random() < 0.5:
                    tags.append(self.get_weighted_choice(nsfw["pussy"], tags))
                if random.random() < 0.3:
                    tags.append(self.get_weighted_choice(nsfw["sexMod"], tags))
                if random.random() < 0.5:
                    tags.append(self.get_weighted_choice(nsfw["sexActionMode"], tags))
                if random.random() < 0.1:
                    tags.append(self.get_weighted_choice(nsfw["bdsm"], tags))
                if random.random() < 0.2:
                    tags.append(self.get_weighted_choice(nsfw["sexAccessories"], tags))
                tags.extend(features)
        if random.random() < 0.4 and enable_moods:
            # 心情
            tags.append("[" + self.get_weighted_choice(rankMoods, tags) + "]")
        if random.random() < 0.4 and enable_identity:
            # 身份
            tags.append("[" + self.get_weighted_choice(rankIdentity, tags) + "]")
        if random.random() < 0.2 and enable_character:
            # 角色
            tags.append("[" + self.get_weighted_choice(rankCharacter, tags) + "]")
        if random.random() < 0.1:
            bg_color = self.get_weighted_choice(backgroundColor, tags)
            tags.append(bg_color)
            if bg_color == 'scenery' and random.random() < 0.5:
                num_objects = random.randint(1, 3)
                for _ in range(num_objects):
                    tags.append(self.get_weighted_choice(backgroundObjects, tags))
        if random.random() < 0.1:
            tags.append(self.get_weighted_choice(cameraPerspective, tags))
        if random.random() < 0.5:
            tags.append(self.get_weighted_choice(cameraAngle, tags))
        for _ in range(c_count):
            if random.random() < 0.2:
                tags.append(self.get_weighted_choice(nsfw["fu"], tags))
            tags.extend(self.character_features('f', cameraAngle, self.nsfw_enabled, irs))
        for _ in range(d_count):
            tags.extend(self.character_features('m', cameraAngle, self.nsfw_enabled, irs))
        for _ in range(u_count):
            tags.extend(self.character_features('o', cameraAngle, self.nsfw_enabled, irs))
        if random.random() < 0.2:
            num_accessories = random.randint(1, 4)
            if irs == 2:
                num_accessories = random.randint(1, 3)
            for _ in range(num_accessories):
                tags.append(self.get_weighted_choice(accessories, tags))
        if random.random() < 0.25:
            num_effects = random.randint(1, 3)
            for _ in range(num_effects):
                tags.append(self.get_weighted_choice(effects, tags))
        if random.random() < 0.1:
            tags.append(self.get_weighted_choice(years, tags))
        if random.random() < 0.1:
            tags.append(self.get_weighted_choice(cameraFocus, tags))
        uni_tag = {}
        for tag in tags:
            # 判断是否为多个空格
            if tag.isspace():
                continue
            uni_tag[tag] = 1
        unique_tags = list(uni_tag.keys())
        tags = [tag if random.random() >= 0.02 else '{' + tag + '}' for tag in unique_tags]
        return ', '.join(tags)


if __name__ == '__main__':
    random_prompt_generator = RandomPromptGenerator(nsfw_enabled=True)
    print(random_prompt_generator.generate())
    print(random_prompt_generator.get_weighted_choice([[1, 35], [2, 20], [3, 7]], []))
    print(random_prompt_generator.get_weighted_choice([['m', 30], ['f', 50], ['o', 10]], []))
    print(random_prompt_generator.get_weighted_choice([
        [
            "dsfs",
            5
        ],
        [
            "sdfsd",
            5
        ]
    ],
        []
    ))
