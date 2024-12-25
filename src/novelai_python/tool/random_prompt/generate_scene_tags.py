import random
from typing import Any, List, Optional, Union

Options = List[List[Union[str, int, Optional[List]]]]

viewF = [
    ["front view", 6],
    ["side view", 6],
    ["three-quarter view", 6],
    ["high-angle view", 6],
    ["bird's-eye view", 2],
    ["low-angle view", 6],
    ["worm's-eye view", 2],
]
focusF = [
    ["solo focus", 6],
    [
        "butt focus",
        6,
        ["headshot portrait", "bust portrait", "half-length portrait"],
    ],
    ["breast focus", 6],
    ["belly focus", 6],
    ["face focus", 6],
]
backgroundCategoriesF = [
    ["landscape", 6],
    ["nature", 6],
    ["scenery", 6],
    ["cityscape", 6],
]
backgroundStyleF = [
    ["detailed background", 30],
    ["detailed background, amazing background", 60],
    ["white background", 2],
    ["grey background", 6],
    ["gradient background", 6],
    ["blurred background", 6],
    ["blue background", 6],
    ["pink background", 6],
    ["black background", 6],
    ["yellow background", 6],
    ["red background", 6],
    ["brown background", 6],
    ["green background", 6],
    ["purple background", 6],
    ["rainbow background", 6],
    ["pattern background", 6],
    ["striped background", 6],
    ["textured background", 6],
    ["abstract background", 1],
    ["spiral background", 6],
    ["tan background", 6],
    ["geometric background", 6],
    ["multicolored background", 6],
    ["forest background", 6],
    ["city background", 6],
    ["simple background", 4],
]
portraitOptionsF = [
    ["headshot portrait", 2],
    ["bust portrait", 2],
    ["half-length portrait", 8],
    ["three-quarter length portrait", 8],
    ["full-length portrait", 4],
    ["close-up", 1],
]
intermediatePortraitsF = [
    "half-length portrait",
    "three-quarter length portrait",
    "full-length portrait",
]
random.shuffle(intermediatePortraitsF)
fullLengthOnlyF = ["full-length portrait"]

artStylesF = [
    ["photorealism", 6],
    ["realistic", 6],
    ["surreal", 6],
    ["abstract", 6],
    ["chibi", 6],
    ["line art", 6],
    ["sketch", 6],
    ["toony", 6],
    ["graphite (artwork)", 4],
    ["watercolor (artwork)", 4],
    ["concept art", 6],
    ["flat colors", 6],
    ["traditional media (artwork)", 6],
    ["oekaki", 6],
    ["minimalism", 6],
    ["simple shading", 6],
    ["cel shading", 6],
    ["soft shading", 6],
    ["cross-hatching", 6],
    ["3d (artwork)", 4],
    ["lineless", 6],
    ["colored pencil (artwork)", 4],
    ["crayon (artwork)", 4],
    ["painting (artwork)", 4],
    ["marker (artwork)", 4],
    ["pen (artwork)", 4],
    ["kemono", 6],
    ["detailed", 6],
    ["digital media (artwork)", 6],
    ["shaded", 6],
]
animalOptionsF = [
    ["domestic dog", 6],
    ["fox", 6],
    ["domestic cat", 6],
    ["equine", 6],
    ["lagomorph", 6],
    ["leporid", 6],
    ["pantherine", 6],
    ["caprine", 6],
    ["rodent", 6],
    ["bovine", 6],
    ["mustelid", 6],
    ["ursine", 6],
    ["bird", 6],
    ["bat", 6],
    ["raccoon", 6],
    ["cetacean", 6],
    ["shark", 6],
    ["theropod", 6],
    ["lizard", 6],
    ["snake", 6],
    ["marsupial", 6],
    ["proboscidean", 6],
    ["primate", 6],
    ["hedgehog", 6],
    ["sciurid", 6],
    ["sus (pig)", 6],
    ["hyena", 6],
    ["ailurid", 6],
    ["crocodilian", 6],
    ["macropod", 6],
    ["insect", 6],
    ["giraffid", 6],
    ["corvid", 6],
    ["turtle", 6],
    ["passerine", 6],
    ["owl", 6],
    ["tanuki", 6],
    ["anseriform", 6],
    ["bee", 6],
    ["mollusk", 6],
    ["arachnid", 6],
    ["fish", 6],
    ["naga", 6],
    ["frog", 6],
    ["western dragon", 6],
    ["unicorn", 6],
    ["eastern dragon", 6],
    ["gryphon", 6],
    ["pegasus", 6],
    ["amphibian", 6],
    ["wyvern", 2],
    ["hippogriff", 4],
    ["hydra, multi head", 2],
    ["hellhound", 6],
    ["chimera", 6],
    ["phoenix, bird", 2],
    ["crustacean", 2],
    ["wolf", 6],
    ["camelid", 2],
    ["cephalopod", 2],
    ["gastropod", 2],
    ["pinniped", 2],
    ["beaver", 2],
    ["capybara", 2],
    ["rat", 2],
    ["squirrel", 2],
    ["hamster", 2],
    ["chipmunk", 2],
    ["reptile", 6],
    ["dinosaur", 2],
    ["chameleon", 2],
    ["gecko", 2],
    ["pterosaur", 2],
    ["bear", 6],
    ["giant panda", 2],
    ["canine", 6],
    ["feline", 6],
    ["moth", 6],
    ["ambiguous species", 4],
]
characterTypesF = [
    ["anthro", 24],
    ["humanoid", 4],
    ["feral", 12],
    ["animal humanoid", 6],
    ["were", 6],
    ["demon", 2],
    ["taur", 4],
    ["robot", 2],
    ["alien", 2],
    ["monster", 2],
    ["undead", 2],
    ["elemental creature", 2],
    ["angel", 2],
    ["mythological creature", 6],
    ["spirit", 2],
    ["diety", 2],
    ["waddling head", 1],
    ["draconopede", 1],
]
mythicalRacesF = [
    ["elf", 6],
    ["demon", 6],
    ["angel", 6],
    ["orc", 6],
    ["goblin", 6],
    ["ogre", 6],
    ["troll (mythology)", 6],
    ["halfling", 6],
    ["imp", 6],
    ["monstrous humanoid", 6],
    ["alien", 6],
    ["flora fauna", 6],
    ["undead", 6],
    ["elemental creature", 6],
    ["skeleton", 6],
    ["human", 6],
    ["mineral fauna", 6],
    ["food creature", 6],
    ["goo creature", 6],
    ["robot", 6],
    ["monster", 6],
    ["ghost", 6],
    ["human", 6],
    ["merfolk", 6],
    ["harpy", 6],
    ["lamia", 6],
    ["oni", 6],
    ["spirit", 6],
]
hybridSpeciesF = [
    ["centaur", 12],
    ["kobold", 12],
    ["sergal", 6],
    ["protogen", 6],
    ["animate inanimate", 1],
    ["avali", 4],
    ["minotaur", 6],
]
bodyColorsF = [
    ["dark body", 6],
    ["light body", 6],
    ["black body", 6],
    ["brown body", 6],
    ["gold body", 6],
    ["green body", 6],
    ["grey body", 6],
    ["orange body", 6],
    ["pink body", 6],
    ["purple body", 6],
    ["red body", 6],
    ["silver body", 6],
    ["tan body", 6],
    ["teal body", 6],
    ["white body", 6],
    ["yellow body", 6],
]
eyeColorsF = [
    ["amber eyes", 6],
    ["black eyes", 6],
    ["blue eyes", 6],
    ["brown eyes", 6],
    ["green eyes", 6],
    ["grey eyes", 6],
    ["orange eyes", 6],
    ["pink eyes", 6],
    ["purple eyes", 6],
    ["red eyes", 6],
    ["silver eyes", 6],
    ["teal eyes", 6],
    ["white eyes", 6],
    ["yellow eyes", 6],
]
scleraColorsF = [
    ["amber sclera", 6],
    ["black sclera", 6],
    ["blue sclera", 6],
    ["brown sclera", 6],
    ["cyan sclera", 6],
    ["green sclera", 6],
    ["grey sclera", 6],
    ["orange sclera", 6],
    ["pink sclera", 6],
    ["purple sclera", 6],
    ["red sclera", 6],
    ["yellow sclera", 6],
]
eyeFeaturesF = [
    ["<3 eyes", 6],
    ["beady eyes", 6],
    ["big eyes", 6],
    ["cute eyes", 6],
    ["empty eyes", 6],
    ["glistening eyes", 6],
    ["glowing eyes", 6],
    ["lidded eyes", 6],
    ["ringed eyes", 4],
    ["simple eyes", 6],
    ["dot eyes", 6],
    ["small eyes", 6],
    ["spiral eyes", 4],
    ["star eyes", 6],
    ["vertical bar eyes", 6],
    ["slit pupils", 3],
]
hairColorsF = [
    ["auburn hair", 6],
    ["black hair", 6],
    ["blonde hair", 6],
    ["blue hair", 6],
    ["brown hair", 6],
    ["cream hair", 6],
    ["green hair", 6],
    ["grey hair", 6],
    ["orange hair", 6],
    ["pink hair", 6],
    ["purple hair", 6],
    ["red hair", 6],
    ["silver hair", 6],
    ["tan hair", 6],
    ["teal hair", 6],
    ["white hair", 6],
]
hairEffectsF = [
    ["multicolored hair", 6],
    ["gradient hair", 6],
    ["hair highlights", 6],
    ["spotted hair", 6],
    ["striped hair", 6],
]
hairLengthsF = [
    ["long hair", 24],
    ["medium hair", 24],
    ["short hair", 24],
    ["bald", 1],
]
hairStylesF = [
    ["afro", 6],
    ["bob cut", 6],
    ["bowl cut", 6],
    ["braided hair", 6],
    ["dreadlocks", 6],
    ["drill curls", 6],
    ["fauxhawk", 6],
    ["hair bun", 6],
    ["hair buns", 6],
    ["mohawk (hairstyle)", 6],
    ["pigtails", 6],
    ["pixie cut", 6],
    ["ponytail", 6],
    ["undercut", 6],
    ["twintails (hairstyle)", 6],
    ["mane hair", 2],
]
hairTexturesF = [
    ["big hair", 6],
    ["curled hair", 6],
    ["fluffy hair", 6],
    ["glistening hair", 6],
    ["glowing hair", 2],
    ["messy hair", 6],
    ["spiky hair", 6],
    ["tentacle hair", 2],
    ["liquid hair", 1],
    ["goo hair", 1],
    ["plant hair", 1],
    ["flaming hair", 2],
    ["wavy hair", 6],
]
hairSpecificsF = [
    ["ahoge", 6],
    ["blunt bangs", 6],
    ["crossed bangs", 6],
    ["hair over eye", 6],
    ["hair over eyes", 6],
]
chestSizesF = [
    ["flat chested", 3],
    ["small breasts", 6],
    ["medium breasts", 6],
    ["big breasts", 3],
    ["huge breasts", 2],
]
bodyFeaturesF = [
    ["collarbone", 6],
    ["small waist", 6],
    ["wide hips", 6],
    ["thigh gap", 2],
    ["3 eyes", 2],
    ["1 eye", 3],
    ["multi eye", 2],
    ["multi arm", 2],
    ["multi horn", 2],
    ["multi tail", 2],
    ["multi wing", 2],
    ["thick eyebrows", 6],
    ["thick eyelashes", 6],
    ["teeth", 6],
    ["overweight", 6],
    ["stocky", 6],
    ["slightly chubby", 6],
    ["muscular", 6],
    ["slim", 6],
    ["athletic", 6],
    ["short", 6],
    ["tall", 6],
    ["musclegut", 6],
    ["big muscles", 6],
    ["curvy figure", 6],
    ["hourglass figure", 6],
    ["pear-shaped figure", 6],
    ["voluptuous", 6],
    ["short stack", 6],
    ["teapot (body type)", 6],
    ["girly", 6],
    ["manly", 6],
    ["mature", 6],
    ["young", 6],
    ["old", 6],
    ["small butt", 6],
    ["big butt", 6],
    ["huge butt", 2],
    ["beauty mark", 6],
    ["freckles", 6],
    ["abs", 6],
    ["biceps", 6],
    ["skinny", 6],
    ["thick arms", 6],
    ["thick lips", 1],
    ["lips", 1],
    ["body hair", 6],
    ["glistening body", 6],
    ["glowing body", 6],
    ["metallic body", 6],
    ["mottled body", 6],
    ["spotted body", 6],
    ["striped body", 6],
    ["translucent body", 6],
    ["markings", 6],
    ["feathers", 6],
    ["fur", 6],
    ["eye scar", 2],
    ["scar", 2],
    ["scales", 6],
    ["long eyelashes", 6],
    ["tail", 6],
    ["bioluminescence", 6],
    ["long ears", 2],
    ["big ears", 2],
    ["pivoted ears", 2],
    ["dipstick ears", 2],
    ["floppy ears", 2],
]
hatsF = [
    ["hat", 36],
    ["bowler hat", 6],
    ["fedora", 6],
    ["top hat", 6],
    ["aviator cap", 6],
    ["biker cap", 6],
    ["chef hat", 6],
    ["cowboy hat", 6],
    ["hard hat", 6],
    ["nurse hat", 6],
    ["police hat", 6],
    ["santa hat", 6],
    ["staw hat", 6],
    ["ushanka", 6],
    ["witch hat", 6],
    ["wizard hat", 6],
    ["beanie", 6],
    ["beret", 6],
    ["baseball cap", 6],
    ["dunce cap", 6],
    ["flat cap", 6],
    ["jester cap", 6],
    ["party hat", 6],
    ["sun hat", 6],
    ["helmet", 8],
    ["cabbie hat", 6],
    ["circlet", 6],
    ["crown", 6],
    ["diadem", 6],
    ["tiara", 6],
    ["bandana", 6],
    ["bonnet", 6],
]
hairAccessoriesF = [
    ["hair ribbon", 6],
    ["hair bow", 6],
    ["hairband", 6],
    ["headdress", 6],
    ["veil", 6],
    ["hooded cloak", 6],
]
dressesF = [
    ["dress", 24],
    ["short dress", 18],
    ["long dress", 18],
    ["christmas dress", 6],
    ["chinese dress", 6],
    ["cocktail dress", 6],
    ["evening gown", 6],
    ["nurse dress", 6],
    ["sundress", 6],
    ["wedding dress", 6],
    ["backless dress", 6],
    ["frilly dress", 6],
    ["slit dress", 6],
    ["strapless dress", 6],
    ["turtleneck dress", 6],
    ["pattern dress", 6],
    ["tight dress", 6],
    ["halter dress", 6],
    ["tube dress", 6],
    ["collared dress", 6],
    ["sailor dress", 6],
    ["gown", 6],
    ["dirndl", 6],
    ["sweater dress", 6],
    ["fur-trimmed dress", 6],
    ["latex dress", 6],
    ["layered dress", 6],
    ["ribbed dress", 6],
    ["ribbon-trimmed dress", 6],
    ["see-through dress", 6],
    ["sleeveless dress", 6],
    ["fundoshi", 6],
    ["hakama", 6],
    ["kimono", 6],
    ["yukata", 6],
    ["furisode", 6],
]
legWearF = [
    ["leggings", 6],
    ["leg warmers", 6],
    ["pantyhose", 6],
    ["stockings", 6],
    ["tights", 6],
    ["thigh highs", 6],
    ["socks", 6],
    ["loose socks", 6],
    ["knee socks", 6],
    ["thigh socks", 6],
    ["ankle socks", 6],
]
topsF = [
    ["blouse", 6],
    ["frilled shirt", 6],
    ["sleeveless shirt", 6],
    ["bustier", 6],
    ["crop top", 6],
    ["camisole", 6],
    ["babydoll", 6],
    ["chemise", 6],
    ["nightgown", 6],
    ["cardigan", 6],
    ["cardigan", 6],
    ["cardigan vest", 6],
    ["coat", 6],
    ["fur coat", 6],
    ["fur-trimmed coat", 6],
    ["long coat", 6],
    ["overcoat", 6],
    ["raincoat", 6],
    ["trenchcoat", 6],
    ["winter coat", 6],
    ["compression shirt", 6],
    ["hoodie", 6],
    ["criss-cross halter", 6],
    ["jacket", 6],
    ["blazer", 6],
    ["cropped jacket", 6],
    ["letterman jacket", 6],
    ["suit jacket", 6],
    ["leather jacket", 6],
    ["poncho", 6],
    ["shirt", 6],
    ["collared shirt", 6],
    ["dress shirt", 6],
    ["off-shoulder shirt", 6],
    ["sleeveless shirt", 6],
    ["striped shirt", 6],
    ["t-shirt", 6],
    ["surcoat", 6],
    ["sweater", 6],
    ["turtleneck", 6],
    ["sleeveless turtleneck", 6],
    ["ribbed sweater", 6],
    ["aran sweater", 6],
    ["argyle sweater", 6],
    ["virgin killer sweater", 6],
    ["tabard", 6],
    ["tailcoat", 6],
    ["tank top", 6],
    ["tube top", 6],
    ["bandeau", 6],
    ["underbust", 6],
    ["vest", 6],
    ["sweater vest", 6],
    ["waistcoat", 6],
    ["chest wraps", 6],
    ["front-tie top", 6],
    ["jersey", 6],
    ["baggy shirt", 6],
    ["polo shirt", 6],
    ["undershirt", 6],
    ["keyhole turtleneck", 6],
]
pantsAndShortsF = [
    ["bloomers", 6],
    ["buruma", 6],
    ["chaps", 6],
    ["kilt", 6],
    ["pants", 6],
    ["tight pants", 6],
    ["baggy pants", 6],
    ["bell-bottoms", 6],
    ["capri pants", 6],
    ["jeans", 6],
    ["rolled up pants", 6],
    ["pelvic curtain", 6],
    ["petticoat", 6],
    ["shorts", 6],
    ["denim shorts", 6],
    ["dolphin shorts", 6],
    ["gym shorts", 6],
    ["micro shorts", 6],
    ["short shorts", 6],
    ["suspender shorts", 6],
    ["skirt", 6],
    ["high-waist skirt", 6],
    ["long skirt", 6],
    ["microskirt", 6],
    ["miniskirt", 6],
    ["overall skirt", 6],
    ["plaid skirt", 6],
    ["pleated skirt", 6],
    ["suspender skirt", 6],
    ["sweatpants", 6],
    ["camo pants", 6],
    ["cargo pants", 6],
    ["harem pants", 6],
    ["leather pants", 6],
    ["sagging pants", 6],
    ["booty shorts", 6],
    ["cargo shorts", 6],
    ["daisy dukes", 6],
    ["hot pants", 6],
    ["short shorts", 6],
    ["track shorts", 6],
    ["grass skirt", 6],
]
footwearF = [
    ["boots", 6],
    ["ankle boots", 6],
    ["cowboy boots", 6],
    ["knee boots", 6],
    ["high heel boots", 6],
    ["lace-up boots", 6],
    ["rubber boots", 6],
    ["thigh boots", 6],
    ["dress shoes", 6],
    ["flats", 6],
    ["high heels", 6],
    ["loafers", 6],
    ["mary janes", 6],
    ["platform footwear", 6],
    ["pointy footwear", 6],
    ["pumps", 6],
    ["sandals", 6],
    ["flip-flops", 6],
    ["geta", 6],
    ["gladiator sandals", 6],
    ["slippers", 6],
    ["animal slippers", 6],
    ["ballet slippers", 6],
    ["crocs", 6],
    ["sneakers", 6],
    ["high tops", 6],
    ["converse", 6],
    ["toeless footwear", 6],
    ["wedge heels", 6],
    ["footwear", 6],
]
specialtyClothingF = [
    ["armor", 6],
    ["power armor", 6],
    ["armored dress", 6],
    ["bikini armor", 6],
    ["cassock", 6],
    ["cheerleader", 6],
    ["ghost costume", 6],
    ["business suit", 6],
    ["pant suit", 6],
    ["skirt suit", 6],
    ["black tie (suit)", 6],
    ["gym uniform", 6],
    ["harem outfit", 6],
    ["hazmat suit", 6],
    ["maid", 6],
    ["miko", 6],
    ["military uniform", 6],
    ["overalls", 6],
    ["pajamas", 6],
    ["pilot suit", 6],
    ["santa costume", 6],
    ["school uniform", 6],
    ["serafuku", 6],
    ["track suit", 6],
    ["tutu", 6],
    ["waitress", 6],
    ["cowboy outfit", 6],
    ["magical girl", 6],
    ["lab coat", 6],
    ["police", 6],
    ["race queen", 6],
    ["bride", 6],
    ["knight", 6],
    ["tomboy", 6],
    ["soccer uniform", 6],
    ["employee uniform", 6],
    ["dancer", 6],
    ["spacesuit", 6],
    ["gyaru", 6],
    ["kogal", 6],
    ["soldier", 6],
    ["pirate", 6],
    ["princess", 6],
    ["samurai", 6],
    ["priest", 6],
    ["nun", 6],
    ["baseball uniform", 6],
    ["basketball uniform", 6],
    ["firefighter uniform", 6],
]
bodysuitsAndRobesF = [
    ["bikesuit", 6],
    ["racing suit", 6],
    ["bodysuit", 6],
    ["jumpsuit", 6],
    ["leotard", 6],
    ["thong leotard", 6],
    ["robe", 6],
    ["unitard", 6],
    ["onesie", 6],
    ["coveralls", 6],
    ["prison uniform", 6],
]
swimwearF = [
    ["swimwear", 6],
    ["swimsuit", 6],
    ["one-piece swimsuit", 6],
    ["square bikini", 6],
    ["school swimsuit", 6],
    ["bikini", 6],
    ["string bikini", 6],
    ["micro bikini", 6],
    ["thong bikini", 6],
    ["sports bikini", 6],
    ["swim briefs", 6],
    ["wetsuit", 6],
    ["front-tie bikini top", 6],
    ["strapless bikini", 6],
    ["maid bikini", 6],
    ["swim trunks", 6],
    ["bikini thong", 6],
    ["speedo", 6],
]
clothingItemsF = [
    ["apron", 6],
    ["cape", 6],
    ["capelet", 6],
    ["hood", 6],
    ["bodystocking", 6],
    ["ascot", 6],
    ["bowtie", 6],
    ["choker", 6],
    ["collar", 6],
    ["epaulettes", 6],
    ["feather boa", 6],
    ["lapels", 6],
    ["neckerchief", 6],
    ["necklace", 6],
    ["necktie", 6],
    ["neck ribbon", 6],
    ["scarf", 6],
    ["shawl", 6],
    ["anklet", 6],
    ["armband", 6],
    ["armlet", 6],
    ["bracelet", 6],
    ["bangle", 6],
    ["spiked bracelet", 6],
    ["bridal gauntlets", 6],
    ["detached sleeves", 6],
    ["arm warmers", 6],
    ["gloves", 6],
    ["fingerless gloves", 6],
    ["elbow gloves", 6],
    ["mittens", 6],
    ["ring", 6],
    ["wide sleeves", 6],
    ["wristband", 6],
    ["wrist cuffs", 6],
    ["ankle cuffs", 6],
    ["wrist scrunchie", 6],
    ["belly chain", 6],
    ["belt", 6],
    ["brooch", 6],
    ["buttons", 6],
    ["corsage", 6],
    ["cuff links", 6],
    ["sarong", 6],
    ["sash", 6],
    ["suspenders", 6],
    ["tassel", 6],
    ["cutout", 6],
    ["frills", 6],
    ["gold trim", 6],
    ["lace trim", 6],
    ["see-through", 6],
    ["torn clothes", 6],
    ["earrings", 6],
    ["hoop earrings", 6],
    ["stud earrings", 6],
    ["glasses", 6],
    ["monocle", 6],
    ["hair accessory", 12],
    ["hairclip", 6],
    ["hair scrunchie", 6],
    ["mask", 6],
    ["surgical mask", 6],
    ["rolled up sleeves", 6],
    ["short sleeves", 6],
    ["long sleeves", 6],
    ["long sleeves", 6],
    ["sleeves past wrists", 6],
    ["puffy sleeves", 6],
    ["sleeveless", 6],
    ["goggles", 6],
    ["sunglasses", 6],
    ["ski goggles", 6],
    ["ear piercing", 6],
    ["eyebrow piercing", 6],
    ["lip piercing", 6],
    ["nose piercing", 6],
    ["tongue piercing", 6],
    ["navel piercing", 6],
    ["zipper", 6],
    ["zettai ryouiki", 6],
    ["wristwatch", 6],
    ["wet", 6],
    ["weapon", 6],
    ["wand", 6],
    ["waist apron", 6],
    ["vambraces", 6],
    ["valentine", 6],
    ["under boob", 6],
    ["umbrella", 6],
    ["unbuttoned", 6],
    ["tray", 6],
    ["tentacles", 6],
    ["tattoo", 6],
    ["sweat", 6],
    ["striped", 6],
    ["off shoulder", 6],
    ["star print", 6],
    ["side boob", 6],
    ["side slit", 6],
    ["shoulder bag", 6],
    ["shirt tucked in", 6],
    ["glistening clothing", 6],
    ["sharp teeth", 6],
    ["sharp fingernails", 6],
    ["saliva", 6],
    ["pouch", 6],
    ["polka dot", 6],
    ["pom poms", 6],
    ["pockets", 6],
    ["skimpy", 6],
    ["ribbons", 6],
    ["plaid", 6],
    ["pendant", 6],
    ["pauldrons", 6],
    ["partially clothed", 6],
    ["neck bell", 6],
    ["navel cutout", 6],
    ["mustache", 6],
    ["wings", 6],
    ["low wings", 6],
    ["lipstick", 6],
    ["leash", 6],
    ["lace", 6],
    ["knee pads", 6],
    ["jewelry", 6],
    ["horn", 6],
    ["curled horn", 6],
    ["midriff", 6],
    ["makeup", 6],
    ["long fingernails", 6],
    ["halo", 6],
    ["gauntlets", 6],
    ["fur trim (clothing)", 6],
    ["fin", 6],
    ["fangs", 6],
    ["facial hair", 6],
    ["eyeshadow", 6],
    ["eyepatch", 6],
    ["eyeliner", 6],
    ["eyelashes", 6],
    ["eyebrows", 6],
    ["eyewear on head", 6],
    ["earmuffs", 6],
    ["corset", 6],
    ["cleavage cutout", 6],
    ["cleavage", 6],
    ["claws", 6],
    ["breasts apart", 6],
    ["breastplate", 6],
    ["bracer", 6],
    ["blood on clothing", 2],
    ["blood on face", 2],
    ["blindfold", 6],
    ["bare shoulders", 6],
    ["bare legs", 6],
    ["band-aid on face", 6],
    ["band-aid", 6],
    ["bandage", 6],
    ["bandaged arm", 6],
    ["bandaged leg", 6],
    ["backpack", 6],
    ["backless clothing", 6],
    ["arm tattoo", 6],
    ["animal print", 6],
    ["clothing around waist", 6],
    ["headphones around neck", 6],
    ["oversized clothing", 6],
    ["greaves", 6],
    ["polka dot bow", 6],
    ["harness", 6],
    ["forehead gem", 6],
    ["spiked collar", 6],
    ["striped necktie", 6],
    ["arm guards", 6],
    ["latex", 6],
    ["bead necklace", 6],
    ["motorcycle", 6],
    ["macro", 6],
    ["cyborg", 6],
    ["bruise", 6],
    ["bruised", 6],
    ["chest gem", 6],
    ["v-neck", 6],
    ["plaid scarf", 6],
    ["prosthetic", 6],
    ["mechanical arm", 6],
    ["blood on hand", 2],
    ["band-aid on nose", 6],
    ["robot joints", 6],
    ["zombie", 6],
    ["tail ribbon", 6],
    ["lanyard", 6],
    ["amputee", 6],
    ["bra strap", 6],
    ["missing arm", 6],
    ["money", 6],
    ["revolver", 6],
    ["pearl necklace", 6],
    ["back dimples", 6],
    ["chest harness", 6],
    ["slime", 6],
    ["partially unzipped", 6],
    ["bodypaint", 6],
    ["metal collar", 6],
    ["loose necktie", 6],
    ["clover", 6],
    ["markings", 6],
    ["mechanical wings", 6],
    ["mascara", 6],
    ["wounded", 6],
    ["jacket around waist", 6],
    ["blood", 2],
    ["rectangular eyewear", 6],
    ["chain necklace", 6],
    ["tie clip", 6],
    ["gold chain", 6],
    ["mechanical parts", 6],
    ["seamed legwear", 6],
    ["eye mask", 6],
    ["scratches", 6],
    ["cross scar", 6],
    ["tusks", 6],
    ["sun symbol", 6],
    ["energy wings", 6],
    ["sweatband", 6],
    ["glowing sword", 6],
    ["fanny pack", 6],
    ["energy ball", 6],
    ["scepter", 6],
    ["cherry blossom print", 6],
    ["insect wings", 6],
    ["utility belt", 6],
    ["fake ears", 6],
    ["magic user", 6],
    ["dark magic", 6],
    ["holy spellcaster", 6],
    ["tribal spellcaster", 6],
    ["adventurer", 6],
    ["goth", 6],
    ["visor", 6],
    ["superhero", 6],
    ["warrior", 6],
    ["thief", 6],
]
facialExpressionsF = [
    ["wince", 6],
    ["wide eyed", 6],
    ["tears", 6],
    ["triangle mouth", 6],
    ["trembling", 6],
    ["tongue out", 6],
    ["sweatdrop", 6],
    ["surprised", 6],
    ["spoken heart", 6],
    ["spoken question mark", 6],
    ["spoken ellipsis", 6],
    ["smug", 6],
    ["smirk", 6],
    ["smile", 6],
    ["serious", 6],
    ["pouting", 6],
    ["parted lips", 6],
    ["o_o", 6],
    ["nose blush", 6],
    ["naughty face", 6],
    ["light smile", 6],
    ["light blush", 6],
    ["licking lips", 6],
    ["laughing", 6],
    ["panting", 6],
    ["happy", 6],
    ["half-closed eyes", 6],
    ["grin", 6],
    ["frown", 6],
    ["flying sweatdrops", 6],
    ["expressionless", 6],
    ["evil grin", 6],
    ["embarrassed", 6],
    ["drunk", 6],
    ["crying", 6],
    ["eyes closed", 6],
    ["clenched teeth", 6],
    ["blush stickers", 6],
    ["blush", 6],
    ["angry", 6],
    ["cross-popping vein", 6],
    ["ahegao", 1],
    ["^_^", 6],
    ["spiral eyes", 6],
    ["question mark", 6],
    [">:)", 6],
    ["=_=", 6],
    [";d", 6],
    [";)", 6],
    ["tongue out", 6],
    [":o", 6],
    [":d", 6],
    [":3", 6],
    ["ellipsis", 6],
    ["?!", 6],
    ["exclamation point", 6],
    ["annoyed", 6],
    ["spoken exclamation mark", 6],
    ["sad", 6],
    ["nervous", 6],
    ["seductive", 6],
    ["bedroom eyes", 6],
    ["zzz", 6],
    ["sleepy", 6],
    ["ear blush", 6],
    ["tired", 6],
    ["nervous sweat", 6],
    ["spoken musical note", 6],
    ["glare", 6],
    ["shy", 6],
    ["nervous smile", 6],
    ["thinking", 6],
    ["puckered lips", 6],
    ["screaming", 6],
    ["grimace", 6],
    ["confused", 6],
    ["worried", 6],
    ["raised eyebrows", 6],
    ["raised eyebrow", 6],
    ["cross-eyed", 6],
    ["narrowed eyes", 6],
    ["stare", 6],
    ["wide eyed", 6],
    ["wink", 6],
    ["furrowed brow", 6],
    ["dilated pupils", 6],
    ["scowl", 6],
    ["sneer", 6],
    ["open smile, open mouth", 6],
    ["open frown, open mouth", 6],
    ["closed smile, mouth closed", 6],
    ["closed frown, mouth closed", 6],
    ["bored", 6],
    ["disgust", 6],
    ["disturbed", 6],
    ["flustered", 6],
    ["grumpy", 6],
    ["guilty", 6],
    ["fear", 6],
    ["love", 6],
    ["lust", 6],
    ["proud", 6],
    ["scared", 6],
    ["shocked", 6],
    ["unimpressed", 6],
]
yearsF = [
    ["year 2005", 6],
    ["year 2006", 6],
    ["year 2007", 6],
    ["year 2008", 6],
    ["year 2009", 6],
    ["year 2010", 6],
    ["year 2011", 6],
    ["year 2012", 6],
    ["year 2013", 6],
    ["year 2014", 6],
    ["year 2015", 6],
    ["year 2016", 6],
    ["year 2017", 6],
    ["year 2018", 6],
    ["year 2018", 6],
    ["year 2019", 6],
    ["year 2020", 6],
    ["year 2021", 6],
    ["year 2022", 6],
    ["year 2023", 6],
]
environmentDetailsF = [
    ["wood floor", 6],
    ["window", 6],
    ["wine glass", 6],
    ["water", 6],
    ["wall", 6],
    ["wall (structure)", 6],
    ["underwater", 6],
    ["torii", 6],
    ["tatami", 6],
    ["steam", 6],
    ["starry sky", 6],
    ["stairs", 6],
    ["space", 6],
    ["snow", 6],
    ["snowing", 6],
    ["smoke", 6],
    ["sky", 6],
    ["shadow", 6],
    ["under shade", 6],
    ["sand", 6],
    ["road", 6],
    ["reflection", 6],
    ["raining", 6],
    ["railing", 6],
    ["pool", 6],
    ["palm tree", 6],
    ["onsen", 6],
    ["sea", 6],
    ["night", 6],
    ["nature", 6],
    ["moon", 6],
    ["grass", 6],
    ["full moon", 6],
    ["forest", 6],
    ["field", 6],
    ["fence", 6],
    ["desk", 6],
    ["day", 6],
    ["curtains", 6],
    ["sofa", 6],
    ["cloud", 6],
    ["classroom", 6],
    ["city", 6],
    ["car", 6],
    ["shrub", 6],
    ["building", 6],
    ["bookshelf", 6],
    ["bedroom", 6],
    ["bed", 6],
    ["beach", 6],
    ["bath", 6],
    ["vines", 6],
    ["bamboo", 6],
    ["house", 6],
    ["ruins", 6],
    ["brick wall", 6],
    ["futon", 6],
    ["bridge", 6],
    ["shelf", 6],
    ["street", 6],
    ["castle", 6],
    ["flower field", 6],
    ["skyscraper", 6],
    ["utility pole", 6],
    ["train interior", 6],
    ["evening", 6],
    ["mountainous horizon", 6],
    ["wave", 6],
    ["kitchen", 6],
    ["tower", 6],
    ["waterfall", 6],
    ["library", 6],
    ["puddle", 6],
    ["lake", 6],
    ["store", 6],
    ["fog", 6],
    ["blood moon", 2],
    ["rooftop", 6],
    ["floor", 6],
    ["shore", 6],
    ["ceiling", 6],
    ["city lights", 6],
    ["bamboo forest", 6],
    ["hallway", 6],
    ["moonlight", 6],
    ["dusk", 6],
    ["sink", 6],
    ["tombstone", 6],
    ["hill", 6],
    ["sunrise", 6],
    ["restaurant", 6],
    ["moss", 6],
    ["church", 6],
    ["town", 6],
    ["cave", 6],
    ["veranda", 6],
    ["reflective floor", 6],
    ["alley", 6],
    ["pond", 6],
    ["tree", 6],
    ["landscape", 6],
    ["cityscape", 6],
    ["garden", 6],
    ["mountain", 6],
    ["scenic view", 6],
    ["dungeon", 6],
    ["underground", 6],
    ["partially submerged", 6],
]
smallObjectsF = [
    ["strawberry", 6],
    ["teddy bear", 6],
    ["teacup", 6],
    ["smartphone", 6],
    ["skull", 6],
    ["shield", 6],
    ["scabbard", 6],
    ["school desk", 6],
    ["scythe", 6],
    ["sack", 6],
    ["rose", 6],
    ["rope", 6],
    ["rock", 6],
    ["rifle", 6],
    ["pumpkin", 6],
    ["potted plant", 6],
    ["popsicle", 6],
    ["polearm", 6],
    ["pocky", 6],
    ["plate", 6],
    ["plant", 6],
    ["pen", 6],
    ["phone", 6],
    ["open book", 6],
    ["parasol", 6],
    ["mug", 6],
    ["mecha", 6],
    ["machine", 6],
    ["lollipop", 6],
    ["leaf", 6],
    ["lantern", 6],
    ["lamp", 6],
    ["knife", 6],
    ["key", 6],
    ["katana", 6],
    ["jack-o'-lantern", 6],
    ["instrument", 6],
    ["innertube", 6],
    ["ice cream", 6],
    ["hibiscus", 6],
    ["headset", 6],
    ["headphones", 6],
    ["handgun", 6],
    ["handbag", 6],
    ["hand fan", 6],
    ["gun", 6],
    ["guitar", 6],
    ["gift", 6],
    ["gift box", 6],
    ["gem", 6],
    ["fruit", 6],
    ["food", 6],
    ["flower", 6],
    ["disposable cup", 6],
    ["dagger", 6],
    ["cup", 6],
    ["cross", 6],
    ["controller", 6],
    ["computer", 6],
    ["cigarette", 6],
    ["chopsticks", 6],
    ["chocolate", 6],
    ["chair", 6],
    ["chain", 6],
    ["cellphone", 6],
    ["cellphone", 6],
    ["cannon", 6],
    ["candy", 6],
    ["candle", 6],
    ["can", 6],
    ["camera", 6],
    ["cake", 6],
    ["bucket", 6],
    ["broom", 6],
    ["branch", 6],
    ["box", 6],
    ["bowl", 6],
    ["bottle", 6],
    ["book", 6],
    ["blanket", 6],
    ["blanket", 6],
    ["bench", 6],
    ["bell", 6],
    ["bed sheet", 6],
    ["beads", 6],
    ["beachball", 6],
    ["basket", 6],
    ["balloon", 6],
    ["ball", 6],
    ["axe", 6],
    ["assault rifle", 6],
    ["apple, fruit", 6],
    ["alcohol", 6],
    ["carrot, vegetable", 6],
    ["paintbrush", 6],
    ["tea", 6],
    ["maple leaf", 6],
    ["television", 6],
    ["handcuffs", 6],
    ["doughnut", 6],
    ["water bottle", 6],
    ["bread", 6],
    ["monitor", 6],
    ["handheld console", 6],
    ["earphones", 6],
    ["stool", 6],
    ["smoking pipe", 6],
    ["cookie", 6],
    ["chalkboard", 6],
    ["coin", 6],
    ["syringe", 6],
    ["christmas tree", 6],
    ["rice", 6],
    ["bathtub", 6],
    ["beer", 6],
    ["street lamp", 6],
    ["egg (food)", 6],
    ["cherry, fruit", 6],
    ["cushion", 6],
    ["scissors", 6],
    ["sake", 6],
    ["burger", 6],
    ["coffee", 6],
    ["clipboard", 6],
    ["electric guitar", 6],
    ["cardboard box", 6],
    ["lily (flower)", 6],
    ["pillar", 6],
    ["wine", 6],
    ["laptop", 6],
    ["shopping bag", 6],
    ["whip", 6],
    ["grapes", 6],
    ["grapes", 6],
    ["water gun", 6],
    ["paper lantern", 6],
    ["vase", 6],
    ["whistle", 6],
    ["noodles", 6],
    ["notebook", 6],
    ["suitcase", 6],
    ["bone", 6],
    ["ice cream cone", 6],
    ["elbow pads", 6],
    ["heart-shaped chocolate", 6],
    ["cane", 6],
    ["ladle", 6],
    ["orange (fruit)", 6],
    ["locker", 6],
    ["gears", 6],
    ["crab", 6],
    ["wine bottle", 6],
    ["coffee mug", 6],
    ["machine gun", 6],
    ["trident", 6],
    ["boat", 6],
    ["road sign", 6],
    ["stick", 6],
    ["armchair", 6],
    ["pillow", 6],
    ["tissue box", 6],
    ["jar", 6],
    ["computer keyboard", 6],
    ["thorns", 6],
    ["office chair", 6],
    ["pot", 6],
    ["pole", 6],
    ["test tube", 6],
    ["rapier", 6],
    ["envelope", 6],
    ["banana, fruit", 6],
    ["lemon, fruit", 6],
    ["shotgun", 6],
    ["energy sword", 6],
    ["pizza", 6],
    ["tomato, fruit", 6],
    ["rubber duck", 6],
    ["candy apple", 6],
    ["baozi", 6],
    ["lily pad", 6],
    ["pancake", 6],
    ["beverage can", 6],
    ["vegetable", 6],
    ["trash can", 6],
    ["frying pan", 6],
    ["four-leaf clover", 6],
    ["ramen", 6],
    ["candy cane", 6],
    ["stethoscope", 6],
    ["plastic bag", 6],
    ["bass guitar", 6],
    ["flower pot", 6],
    ["pudding", 6],
    ["soccer ball", 6],
    ["duffel bag", 6],
    ["cigar", 6],
    ["beach towel", 6],
    ["hammer", 6],
    ["glowstick", 6],
    ["coffee cup", 6],
    ["volleyball", 6],
    ["sweets", 6],
    ["pastry", 6],
    ["dessert", 6],
    ["satchel", 6],
    ["torch", 6],
    ["surfboard", 6],
    ["briefcase", 6],
    ["baseball", 6],
    ["barrel", 6],
    ["tulip (flower)", 6],
    ["baseball glove", 6],
]
posesAndActionsF = [
    ["waving", 6],
    ["wariza", 6],
    ["walking", 6],
    ["wading", 6],
    ["ass up", 6],
    ["thought bubble", 6],
    ["dialogue", 6],
    ["stretching", 6],
    ["straddling", 6],
    ["on one leg", 6],
    ["standing", 6],
    ["spread legs", 6],
    ["spread arms", 6],
    ["shirt lift", 6],
    ["selfie", 6],
    ["salute", 6],
    ["restrained", 6],
    ["reaching towards viewer", 6],
    ["reaching", 6],
    ["v sign", 6],
    ["paw pose", 6],
    ["outstretched arm", 6],
    ["outstretched arms", 6],
    ["on back", 6],
    ["on bed", 6],
    ["on chair", 6],
    ["on couch", 6],
    ["on floor", 6],
    ["on one knee", 6],
    ["on side", 6],
    ["on front", 6],
    ["lying", 6],
    ["looking up", 6],
    ["looking aside", 6],
    ["looking down", 6],
    ["looking back", 6],
    ["looking away", 6],
    ["looking at viewer", 6],
    ["licking", 6],
    ["legs up", 6],
    ["legs together", 6],
    ["raised leg", 6],
    ["leaning forward", 6],
    ["leaning backward", 6],
    ["knees up", 6],
    ["knock-kneed", 6],
    ["kneeling", 6],
    ["jumping", 6],
    ["raised index finger", 6],
    ["hugging object", 6],
    ["heart hands", 6],
    ["headpat", 6],
    ["arms above head", 6],
    ["hands on hips", 6],
    ["hand on hip", 6],
    ["hand on face", 6],
    ["hand on chest", 6],
    ["hand in pocket", 6],
    ["raised hand", 6],
    ["hand to mouth", 6],
    ["hand between legs", 6],
    ["pose", 6],
    ["fighting pose", 6],
    ["eating", 6],
    ["drinking", 6],
    ["double v sign", 6],
    ["dancing", 6],
    ["crossed legs", 6],
    ["crossed arms", 6],
    ["covering mouth", 6],
    ["covering breasts", 1],
    ["contrapposto", 6],
    ["clothing pull", 6],
    ["fist", 6],
    ["claw pose", 6],
    ["bent over", 6],
    ["hands behind back", 6],
    ["hands behind head", 6],
    ["arms at sides", 6],
    ["raised arm", 6],
    ["arm support", 6],
    ["holding own arm", 6],
    ["arched back", 6],
    ["all fours", 1],
    ["against surface", 6],
    ["arm under breasts", 6],
    ["on ground", 6],
    ["pigeon toed", 6],
    ["thumbs up", 6],
    ["kick", 6],
    ["hand on thigh", 6],
    ["tiptoes", 6],
    ["singing", 6],
    ["falling", 6],
    ["hand on knee", 6],
    ["punch", 6],
    ["yawn", 6],
    ["hand on stomach", 6],
    ["hand on cheek", 6],
    ["hands on cheeks", 6],
    ["hand on butt", 6],
    ["covering face", 6],
    ["shooting", 6],
    ["shush", 6],
    ["crouching", 6],
    ["feet up", 6],
    ["open hands", 6],
    ["waking up", 6],
    ["hands on knees", 6],
    ["pointing", 6],
    ["pointing up", 6],
    ["pointing at viewer", 6],
    ["holding own arm", 6],
    ["exercise", 6],
    ["finger to cheek", 6],
    ["covering eyes", 6],
    ["beckoning", 6],
    ["rubbing eyes", 6],
    ["praying", 6],
    ["holding sign", 6],
    ["looking at phone", 6],
    ["fleeing", 6],
    ["ok sign", 6],
    ["hands on own thighs", 6],
    ["sleeping", 6],
    ["action pose", 6],
    ["holding object", 6],
    ["flying", 6],
    ["relaxing", 6],
    ["sitting", 6],
    ["gesture", 6],
    ["playing music", 6],
    ["workout", 6],
    ["playing videogame", 6],
]
visualEffectsF = [
    ["sparkles", 6],
    ["snowflake", 6],
    ["petals", 6],
    ["pawprint", 6],
    ["musical note", 6],
    ["motion lines", 6],
    ["magic", 6],
    ["light rays", 6],
    ["lens flare", 6],
    ["ice", 6],
    ["glowing", 6],
    ["glint", 6],
    ["fire", 6],
    ["fantasy", 6],
    ["falling petals", 6],
    ["emphasis lines", 6],
    ["electricity", 6],
    ["depth of field", 6],
    ["crystal", 6],
    ["confetti", 6],
    ["chromatic aberration", 6],
    ["christmas", 6],
    ["cherry blossom", 6],
    ["bubble", 6],
    ["autumn", 6],
    ["aura", 6],
    ["explosion", 6],
    ["summer", 6],
    ["sunbeam", 6],
    ["magic circle", 6],
    ["fireworks", 6],
    ["winter", 6],
    ["partially colored", 6],
    ["ripples", 6],
    ["rainbow", 6],
    ["sepia", 6],
    ["blood splatter", 2],
    ["spring (season)", 6],
    ["rose petals", 6],
    ["shiny", 6],
    ["lightning", 6],
    ["blue fire", 6],
    ["falling leaves", 6],
    ["muted color", 6],
    ["soap bubbles", 6],
    ["horror (theme)", 6],
    ["colorful", 6],
    ["constellation", 6],
    ["egyptian", 6],
    ["surreal", 6],
    ["paint splatter", 6],
    ["lolita (fashion) ", 6],
    ["abstract", 6],
    ["embers", 6],
    ["sunburst", 6],
    ["stage lights", 6],
    ["fashion", 6],
    ["trick or treat", 6],
    ["fluffy", 6],
    ["symmetry", 6],
    ["glitch", 6],
    ["border", 6],
    ["framed", 6],
    ["character image", 6],
    ["3d (artwork)", 6],
    ["line art", 6],
    ["lineless", 6],
    ["outline", 6],
    ["pixel (artwork) ", 6],
    ["oekaki", 6],
    ["screencap", 6],
    ["game cg", 6],
    ["drop shadow", 6],
    ["gradient", 6],
    ["grainy", 6],
    ["film grain", 6],
    ["bokeh", 6],
    ["backlighting", 6],
    ["dithering", 6],
    ["monochrome", 2],
    ["greyscale", 6],
    ["silhouette", 6],
    ["vignette", 6],
    ["art deco", 6],
    ["art nouveau", 6],
    ["science fiction", 6],
    ["steampunk", 6],
    ["cyberpunk", 6],
    ["futuristic", 6],
    ["western", 6],
    ["sunlight", 6],
    ["wind", 6],
    ["restricted palette", 6],
    ["overgrown", 6],
    ["cosmic horror", 6],
    ["halloween", 6],
    ["grass", 6],
    ["blood", 2],
    ["dark theme", 6],
    ["light theme", 6],
    ["foreshortening", 6],
    ["cutaway", 6],
    ["romantic ambiance", 6],
]
colorsF = [
    ["black", 6],
    ["blue", 6],
    ["brown", 6],
    ["green ", 6],
    ["grey", 6],
    ["orange", 6],
    ["pink", 6],
    ["purple", 6],
    ["red", 6],
    ["tan", 6],
    ["teal", 6],
    ["white", 6],
    ["yellow", 6],
    ["multicolored", 2],
    ["rainbow", 2],
    ["two tone", 2],
    ["pattern", 3],
]


def random_range(a, b):
    if a == b:
        return a
    if a > b:
        a, b = b, a
    return random.randint(a, b)


def get_weighted_random_choice(options: Options, tags: List[Any]) -> Any:
    """
    从加权选项中随机选择一项。
    :param options: 元组列表, 每个元组包含一个选项值和其权重。
    :param tags: 当前的 traits，用于条件过滤（虽然实际没有直接用到）。
    :return: 随机选择的选项。
    """
    # 过滤掉有条件选项 (第三个字段) 且条件不满足的项
    filtered_options = [option for option in options if len(option) < 3 or any(tag in tags for tag in option[2])]

    # 总权重
    total_weight = sum(option[1] for option in filtered_options)

    # 生成一个 1 到 total_weight 之间的随机数
    random_weight = random_range(1, total_weight)

    # 根据权重，找到对应选项
    cumulative_weight = 0
    for option in filtered_options:
        cumulative_weight += option[1]
        if random_weight <= cumulative_weight:
            return option[0]

    # 如果没有返回，抛出异常 (不应该达到此处)
    raise RuntimeError("get_weighted_choice: should not reach here")


def generate_character_traits(
        gender: str, portrait_type: str, level: int
) -> tuple:
    """
    生成角色特性。
    :param gender: 性别 (例如 'f' 表示女性)。
    :param portrait_type: word of intermediatePortraitsF or  fullLengthOnlyF
    :param level: 等级 (影响特征和服饰数量)。
    :return: 包含 tags 和 flags。
    """
    traits: List[Any] = []
    flags: List[str] = []

    # 随机选择一个 "种类"
    category = get_weighted_random_choice(
        [
            ["core", 50],
            ["humanoid", 20],
            ["other", 5],
        ],
        traits
    )

    # 根据选择种类，选择不同特征或标志
    if category == "core":
        traits.append(get_weighted_random_choice(animalOptionsF, traits))
        if random.random() < 0.8:
            traits.append(get_weighted_random_choice(characterTypesF, traits))

    elif category == "humanoid":
        traits.append("humanoid")
        traits.append(get_weighted_random_choice(mythicalRacesF, traits))
        flags.append("not_furry")

    elif category == "other":
        traits.append(get_weighted_random_choice(hybridSpeciesF, traits))

    # 随机分支：身体颜色
    if random.random() < 0.7:
        traits.append(get_weighted_random_choice(bodyColorsF, traits))

    # 随机分支：身体风格
    if random.random() < 0.7:
        body_style = get_weighted_random_choice(
            [
                ["multicolored body", 50],
                ["two tone body", 30],
                ["rainbow body", 2],
            ],
            traits
        )

        if body_style in {"multicolored body", "two tone body"} and random.random() < 0.5:
            traits.append(get_weighted_random_choice(bodyColorsF, traits))

        traits.append(body_style)

    # 随机分支：眼睛和其他特性
    if random.random() < 0.7:
        traits.append(get_weighted_random_choice(eyeColorsF, traits))

    if random.random() < 0.05:
        traits.append(get_weighted_random_choice(scleraColorsF, traits))

    if random.random() < 0.1:
        traits.append(get_weighted_random_choice(eyeFeaturesF, traits))

    # 如果标签中含 "not_furry"，处理毛发或发型的特性
    if "not_furry" in flags:
        if random.random() < 0.7:
            traits.append(get_weighted_random_choice(hairLengthsF, traits))
        if random.random() < 0.5:
            traits.append(get_weighted_random_choice(hairStylesF, traits))
        if random.random() < 0.7:
            traits.append(get_weighted_random_choice(hairColorsF, traits))
            if random.random() < 0.1:
                traits.append(get_weighted_random_choice(hairEffectsF, traits))
    else:
        if random.random() < 0.2:
            traits.append(get_weighted_random_choice(hairLengthsF, traits))
        if random.random() < 0.1:
            traits.append(get_weighted_random_choice(hairStylesF, traits))
        if random.random() < 0.1:
            traits.append(get_weighted_random_choice(hairColorsF, traits))
            if random.random() < 0.1:
                traits.append(get_weighted_random_choice(hairEffectsF, traits))

    if "not_furry" in flags:
        if random.random() < 0.1:
            traits.append(get_weighted_random_choice(hairTexturesF, traits))
    else:
        if random.random() < 0.05:
            traits.append(get_weighted_random_choice(hairTexturesF, traits))

    if "not_furry" in flags:
        if random.random() < 0.1:
            traits.append(get_weighted_random_choice(hairSpecificsF, traits))
    else:
        if random.random() < 0.05:
            traits.append(get_weighted_random_choice(hairSpecificsF, traits))

    # 人物性别特征
    if gender == "f" and random.random() < 0.5 and "feral" not in traits:
        traits.append(get_weighted_random_choice(chestSizesF, traits))
    elif gender == "f" and random.random() < 0.1:
        traits.append(get_weighted_random_choice(chestSizesF, traits))

    # 身体特征数量，通过级别决定权重
    body_feature_count = (
        get_weighted_random_choice(
            [
                [0, 10],
                [1, 30],
                [2, 15],
                [3, 5],
            ],
            traits
        )
        if level == 1
        else get_weighted_random_choice(
            [
                [0, 20],
                [1, 40],
                [2, 10],
            ],
            traits
        )
        if level == 2
        else get_weighted_random_choice(
            [
                [0, 30],
                [1, 30],
            ],
            traits
        )
    )

    for _ in range(body_feature_count):
        traits.append(get_weighted_random_choice(bodyFeaturesF, traits))

    # 随机分支: 帽子或头饰
    if random.random() < 0.15:
        traits.append(get_weighted_random_choice(hatsF, traits))
    elif random.random() < 0.2:
        traits.append(get_weighted_random_choice(hairAccessoriesF, traits))

    # 生成服饰相关内容（简化逻辑）
    clothing_type = get_weighted_random_choice(
        [
            ["uniform", 10],
            ["swimsuit", 5],
            ["bodysuit", 5],
            ["normal clothes", 40],
        ],
        traits
    )

    # 处理服饰类型和附加逻辑（如颜色等）
    if "feral" in traits:
        if random.random() > 0.6:
            clothing_type = None
    elif random.random() < 0.2:
        clothing_type = None

    hasIntermediateFeatures = any(e in intermediatePortraitsF for e in traits)

    # 概率分支：30% 概率添加 "furgonomics"
    if clothing_type and random.random() < 0.3:
        traits.append("furgonomics")

    if clothing_type == "uniform":
        traits.append(get_weighted_random_choice(specialtyClothingF, traits))
    elif clothing_type == "swimsuit":
        traits.append(get_weighted_random_choice(swimwearF, traits))
    elif clothing_type == "bodysuit":
        traits.append(get_weighted_random_choice(bodysuitsAndRobesF, traits))
    elif clothing_type == "normal clothes":
        if gender == "f" and random.random() < 0.2:
            addColor = random.random() < 0.5
            color = get_weighted_random_choice(colorsF, traits)
            dress = get_weighted_random_choice(dressesF, traits)
            traits.append(f"{color + ' ' if addColor else ''}{dress}")
        if random.random() < 0.9:
            addColor = random.random() < 0.5
            color = get_weighted_random_choice(colorsF, traits)
            traits.append(f"{color + ' ' if addColor else ''}{get_weighted_random_choice(topsF, traits)}")
        if (
                not hasIntermediateFeatures
                and random.random() < 0.7
                and portrait_type
                and portrait_type in intermediatePortraitsF
        ):
            addColor = random.random() < 0.5
            color = get_weighted_random_choice(colorsF, traits)
            traits.append(f"{color + ' ' if addColor else ''}{get_weighted_random_choice(pantsAndShortsF, traits)}")
        if random.random() < 0.5 and portrait_type and portrait_type in intermediatePortraitsF:
            addColor = random.random() < 0.5
            color = get_weighted_random_choice(colorsF, traits)
            traits.append(f"{color + ' ' if addColor else ''}{get_weighted_random_choice(legWearF, traits)}")
        if random.random() < 0.3 and portrait_type and portrait_type in fullLengthOnlyF:
            addColor = random.random() < 0.5
            color = get_weighted_random_choice(colorsF, traits)
            traits.append(f"{color + ' ' if addColor else ''}{get_weighted_random_choice(footwearF, traits)}")

    # 概率分支：60% 添加 facialExpressionsF
    if random.random() < 0.6:
        traits.append(get_weighted_random_choice(facialExpressionsF, traits))

    # 概率分支：40% 添加 posesAndActionsF
    if random.random() < 0.4:
        traits.append(get_weighted_random_choice(posesAndActionsF, traits))

    # 筛选逻辑：去除某些特定的眼睛特征
    if any(
            "sleeping" in trait or "zzz" in trait or "eyes closed" in trait
            for trait in traits
    ):
        traits = [
            trait
            for trait in traits
            if all(
                trait != eyeOption[0] for eyeOption in eyeColorsF
            )
        ]
        traits = [
            trait
            for trait in traits
            if all(
                trait != scleraOption[0] for scleraOption in scleraColorsF
            )
        ]
        traits = [
            trait
            for trait in traits
            if all(
                trait != eyeFeature[0] for eyeFeature in eyeFeaturesF
            )
        ]

    # 根据 level 确定 clothingItemsCount
    if level == 1:
        clothingItemsCount = get_weighted_random_choice(
            [
                [0, 20],
                [1, 20],
                [2, 10],
                [3, 2],
            ],
            traits,
        )
    elif level == 2:
        clothingItemsCount = get_weighted_random_choice(
            [
                [0, 30],
                [1, 30],
                [2, 5],
            ],
            traits,
        )
    else:
        clothingItemsCount = get_weighted_random_choice(
            [
                [0, 30],
                [1, 15],
            ],
            traits,
        )

    # 添加随机数量的 clothingItemsF 标签
    for _ in range(clothingItemsCount):
        traits.append(get_weighted_random_choice(clothingItemsF, traits))

    # 特定情况下筛除与 "legwear" 和 "legs" 相关的特性
    if hasIntermediateFeatures or (portrait_type and portrait_type not in intermediatePortraitsF):
        traits = [e for e in traits if "legwear" not in e and "legs" not in e]

    return traits, flags


# 核心函数：场景标签生成器
def generate_scene_tags() -> List[str]:
    tags: List[str] = []

    # 随机选择角色数及其权重分布
    character_count = get_weighted_random_choice(
        [
            [1, 80],
            [2, 15],
            [3, 5],
            [0, 5]
        ],
        tags
    )
    if character_count == 0:
        tags.append("zero pictured")
        # 概率分支：30% 概率添加艺术风格
        if random.random() < 0.3:
            tags.append(get_weighted_random_choice(artStylesF, tags))
        tags.append(get_weighted_random_choice(backgroundCategoriesF, tags))

        # 随机环境细节生成
        environment_count = get_weighted_random_choice(
            [
                [2, 15],
                [3, 50],
                [4, 15],
                [5, 5]
            ],
            tags
        )
        for _ in range(environment_count):
            tags.append(
                get_weighted_random_choice(
                    [
                        ["inside", 50],
                        ["outside", 50]
                    ],
                    tags
                )
            )
            tags.append(get_weighted_random_choice(environmentDetailsF, tags))

        # 随机小物件生成
        small_object_count = get_weighted_random_choice(
            [
                [0, 15],
                [1, 20],
                [2, 15],
                [3, 15],
                [4, 10],
                [5, 5]
            ],
            tags
        )
        for _ in range(small_object_count):
            tags.append(get_weighted_random_choice(smallObjectsF, tags))

        return [", ".join(tags)]

    portrait_option = None
    female_count = 0
    male_count = 0
    ambiguous_gender_count = 0

    # 根据角色数随机分配性别
    for _ in range(character_count):
        gender_choice = get_weighted_random_choice(
            [
                ["m", 45],
                ["f", 45],
                ["o", 10]
            ],
            tags
        )
        if gender_choice == "m":
            male_count += 1
        elif gender_choice == "f":
            female_count += 1
        elif gender_choice == "o":
            ambiguous_gender_count += 1

    # 添加标签："solo", "duo", "trio"
    if character_count == 1:
        tags.append("solo")
    elif character_count == 2:
        tags.append("duo")
    elif character_count == 3:
        tags.append("trio")

    # 概率分支：30% 概率添加艺术风格
    if random.random() < 0.3:
        tags.append(get_weighted_random_choice(artStylesF, tags))

    # 根据性别计数添加标签
    if female_count > 0:
        tags.append("female")
    if male_count > 0:
        tags.append("male")
    if ambiguous_gender_count > 0:
        tags.append("ambiguous gender")

    # 概率分支：90% 添加背景样式
    if random.random() < 0.9:
        background_style = get_weighted_random_choice(backgroundStyleF, tags)
        tags.append(background_style)

        # 详细背景样式
        if background_style in {"detailed background", "amazing background"}:
            environment_detail_count = get_weighted_random_choice(
                [
                    [1, 50],
                    [2, 20]
                ],
                tags
            )
            tags.append(
                get_weighted_random_choice(
                    [
                        ["inside", 50],
                        ["outside", 50]
                    ],
                    tags
                )
            )
            for _ in range(environment_detail_count):
                tags.append(get_weighted_random_choice(environmentDetailsF, tags))

    # 概率分支：30% 添加视角标签
    if random.random() < 0.3:
        tags.append(get_weighted_random_choice(viewF, tags))

    # 概率分支：70% 添加肖像选项
    if random.random() < 0.7:
        portrait_option = get_weighted_random_choice(portraitOptionsF, tags)
        if portrait_option:
            tags.append(portrait_option)

    has_furry_elements = False
    character_tags: List[str] = []

    # 根据性别计数生成角色特征
    for _ in range(female_count):
        _tags, _flags = generate_character_traits("f", portrait_option, character_count)
        character_tags.extend(_tags)
        if "not_furry" not in _flags:
            has_furry_elements = True

    for _ in range(male_count):
        _tags, _flags = generate_character_traits("m", portrait_option, character_count)
        character_tags.extend(_tags)
        if "not_furry" not in _flags:
            has_furry_elements = True

    for _ in range(ambiguous_gender_count):
        _tags, _flags = generate_character_traits("o", portrait_option, character_count)
        character_tags.extend(_tags)
        if "not_furry" not in _flags:
            has_furry_elements = True

    # 如果没有毛绒元素，添加 "not furry"
    if not has_furry_elements:
        character_tags.insert(0, "not furry")

    tags.extend(character_tags)

    # 概率分支：20% 添加小物件
    if random.random() < 0.2:
        small_object_count = get_weighted_random_choice(
            [
                [0, 40],
                [1, 20],
                [2, 10],
                [3, 2]
            ],
            tags
        )
        if character_count == 2:
            small_object_count = get_weighted_random_choice(
                [
                    [0, 30],
                    [1, 20],
                    [2, 5]
                ],
                tags
            )
        elif character_count == 3:
            small_object_count = get_weighted_random_choice(
                [
                    [0, 20],
                    [1, 10]
                ],
                tags
            )
        for _ in range(small_object_count):
            tags.append(get_weighted_random_choice(smallObjectsF, tags))

    # 概率分支：25% 添加视觉效果
    if random.random() < 0.25:
        visual_effect_count = get_weighted_random_choice(
            [
                [1, 80],
                [2, 20]
            ],
            tags
        )
        for _ in range(visual_effect_count):
            tags.append(get_weighted_random_choice(visualEffectsF, tags))

    # 概率分支：20% 添加年代标签
    if random.random() < 0.2:
        tags.append(get_weighted_random_choice(yearsF, tags))

    # 概率分支：5% 添加焦点标签
    if random.random() < 0.05:
        tags.append(get_weighted_random_choice(focusF, tags))

    # 消除重复标签并返回
    tags = list({tag: True for tag in tags}.keys())
    return [", ".join(tags)]


if __name__ == "__main__":
    print(generate_scene_tags())
