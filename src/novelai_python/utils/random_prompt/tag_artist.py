# -*- coding: utf-8 -*-
# @Time    : 2024/1/26 下午5:08
# @Author  : sudoskys
# @File    : tag_artist.py
# @Software: PyCharm

rankArtist = [
    [
        "redi_(rasec_asdjh)",
        50
    ],
    [
        "suoiresnu",
        41
    ],
    [
        "kulo_jawa",
        30
    ],
    [
        "sakanaya_(sakanaya952)",
        25
    ],
    [
        "momisan",
        20
    ],
    [
        "tansuan_(ensj3875)",
        19
    ],
    [
        "hitmanatee",
        18
    ],
    [
        "yoru0409",
        18
    ],
    [
        "zovokia",
        14
    ],
    [
        "memeh",
        13
    ],
    [
        "honashi",
        13
    ],
    [
        "pinkmill",
        13
    ],
    [
        "kanjy00u",
        12
    ],
    [
        "eckert&eich",
        12
    ],
    [
        "ningen mame",
        100
    ],
    [
        "ciloranko",
        100
    ],
    [
        "sho (sho lwlw)",
        80
    ],
    [
        "tianliang duohe fangdongye",
        100
    ],
    [
        "alphonse (white datura)",
        80
    ],
    [
        "rei (sanbonzakura)",
        100
    ],
    [
        "mamyouda",
        80
    ],
    [
        "ogipote",
        100
    ],
    [
        "fuzichoco",
        100
    ],
    [
        "norza",
        80
    ],
    [
        "AkiZero1510",
        100
    ],
    [
        "ATDAN",
        100
    ],
    [
        "mignon",
        80
    ],
    [
        "shexyo",
        100
    ],
    [
        "musashi (dishwasher1910)",
        100
    ],
    [
        "modare",
        80
    ],
    [
        "asteroidill",
        80
    ],
    [
        "potg(piotegu)",
        80
    ],
    [
        "kedama milk",
        100
    ],
    [
        "jun (aousa0328)",
        80
    ],
    [
        "sky freedom",
        80
    ],
    [
        "ask (askzy)",
        100
    ],
    [
        "toridamono",
        100
    ],
    [
        "sencha (senchat)",
        80
    ],
    [
        "void_0",
        80
    ],
    [
        "mandrill",
        100
    ],
    [
        "tokkyu",
        100
    ],
    [
        "houkisei",
        80
    ],
    [
        "konya karasue",
        100
    ],
    [
        "akakura",
        100
    ],
    [
        "kawacy",
        100
    ],
    [
        "reoen",
        100
    ],
    [
        "nixeu",
        100
    ],
    [
        "cierra_(ra-bit)",
        100
    ],
    [
        "artistask_(askzy)",
        100
    ],
    [
        "gomzi",
        100
    ],
    [
        "you_shimizu",
        100
    ],
    [
        "demizu_posuka",
        100
    ],
    [
        "asakuraf",
        100
    ],
    [
        "ningen_mame",
        100
    ],
    [
        "sho_(sho_lwlw)",
        100
    ],
    [
        "alphonse_(white_datura)",
        100
    ],
    [
        "rei_(sanbonzakura)",
        100
    ],
    [
        "wlop",
        100
    ],
    [
        "as109",
        100
    ],
    [
        "Milkychu",
        100
    ],
    [
        "Cogecha",
        100
    ],
    [
        "liduke",
        100
    ],
    [
        "infukun",
        100
    ],
    [
        "amazuyu_tatsuki",
        100
    ],
    [
        "Happ\u014dbi Jin",
        100
    ],
    [
        "Rella",
        100
    ],
    [
        "omone hokoma agm",
        100
    ],
    [
        "toosaka asagi",
        100
    ],
    [
        "Mochizuki Kei",
        100
    ],
    [
        "Namie",
        100
    ],
    [
        "Hoji",
        100
    ],
    [
        "sy4",
        100
    ],
    [
        "mika_pikazo",
        100
    ],
    [
        "momoko(momopoco)",
        100
    ],
    [
        "rurudo",
        100
    ],
    [
        "missile228",
        100
    ],
    [
        "miyase_mahiro",
        100
    ],
    [
        "touzai(poppin phl95)",
        100
    ],
    [
        "kukka",
        100
    ],
    [
        "kantoku",
        100
    ],
    [
        "poco(asahi age)",
        100
    ],
    [
        "refeia",
        100
    ],
    [
        "ke-ta",
        100
    ],
    [
        "anmi",
        100
    ],
    [
        "tiv",
        100
    ],
    [
        "chen_bin",
        100
    ],
    [
        "lm7 (op-center)",
        100
    ],
    [
        "shion (mirudakemann)",
        100
    ],
    [
        "asteroid ill",
        100
    ],
    [
        "potg (piotegu)",
        100
    ],
    [
        "KinHasu",
        100
    ],
    [
        "ryou_(ryoutarou)",
        100
    ],
    [
        "mamimi_(mamamimi)",
        100
    ],
]

if __name__ == "__main__":
    var = vars().copy()

    # 获取tags列表
    tags = []
    for key, value in var.items():
        if not key.startswith('_') and key != 'var':
            tags.extend(value)
    print(tags)

    # 展开二级列表
    tags = [tag[0] for tag in tags]
    print(tags)
    import json

    with open('../../../../playground/cos/tag_artist.json', 'w') as f:
        json.dump(tags, f)