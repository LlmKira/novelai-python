import base64
import random
from datetime import datetime
from typing import List, Optional, Any, Union

from pydantic import BaseModel

Options = List[List[Union[str, int, Optional[List]]]]

cameraAngles = [
    ["dutch angle", 5],
    ["from above", 5],
    ["from behind", 5],
    ["from below", 5],
    ["from side", 5],
    ["straight-on", 5],
]
objectFocus = [
    ["solo focus", 5],
    ["ass focus", 5, ["portrait"]],
    ["foot focus", 5, ["portrait", "cowboy shot", "upper body"]],
    ["hip focus", 5, ["portrait"]],
    ["back focus", 5],
    ["breast focus", 5],
    ["armpit focus", 3],
    ["eye focus", 5],
]
sceneTypes = [
    ["landscape", 5],
    ["nature", 5],
    ["scenery", 5],
    ["still life", 5],
    ["cityscape", 5],
]
backgroundStyles = [
    ["white background", 5],
    ["grey background", 5],
    ["gradient background", 7],
    ["blurry background", 5],
    ["blue background", 5],
    ["pink background", 5],
    ["black background", 5],
    ["yellow background", 5],
    ["red background", 5],
    ["two-tone background", 7],
    ["brown background", 5],
    ["green background", 5],
    ["purple background", 5],
    ["orange background", 5],
    ["floral background", 5],
    ["polka dot background", 5],
    ["striped background", 5],
    ["multicolored background", 7],
    ["starry background", 5],
    ["dark background", 5],
    ["checkered background", 5],
    ["aqua background", 5],
    ["beige background", 5],
    ["heart background", 5],
    ["argyle background", 3],
    ["halftone background", 4],
    ["sparkle background", 5],
    ["abstract background", 5],
    ["patterned background", 5],
    ["plaid background", 4],
    ["sunburst background", 4],
    ["tan background", 5],
    ["light blue background", 5],
    ["snowflake background", 5],
    ["grid background", 5],
    ["leaf background", 5],
    ["rainbow background", 5],
    ["lavender background", 5],
    ["light brown background", 5],
    ["monochrome background", 5],
    ["bubble background", 5],
    ["sepia background", 5],
    ["fiery background", 5],
    ["silver background", 5],
    ["splatter background", 5],
    ["sketch background", 5],
    ["scenery", 100],
]
framingStyles = [
    ["portrait", 4],
    ["upper body", 5],
    ["cowboy shot", 3],
    ["full body", 4],
    ["close-up", 1],
    ["split crop", 1],
]
artStyles = [
    ["ligne claire", 5],
    ["realistic", 5],
    ["sketch", 5],
    ["jaggy lines", 5],
    ["retro artstyle", 5],
    ["toon (style)", 5],
    ["western comics (style)", 5],
    ["surreal", 5],
    ["abstract", 5],
    ["spot color", 5],
    ["graphite (medium)", 5],
    ["watercolor (medium)", 5],
    ["concept art", 5],
    ["flat color", 5],
    ["ai-generated", 5],
    ["faux traditional media", 5],
    ["oekaki", 5],
    ["jaggy lines", 5],
    ["minimalism", 5],
    ["impressionism", 5],
    ["1970s (style)", 5],
    ["1980s (style)", 5],
    ["1990s (style)", 5],
]
animalFeatures = [
    ["bat ears, bat wings", 5],
    ["bear ears", 5],
    ["rabbit ears", 5],
    ["cat ears, cat tail", 5],
    ["cow ears, cow horns, cow tail", 5],
    ["deer ears, deer antlers", 5],
    ["dog ears, dog tail", 5],
    ["fox ears, fox tail", 5],
    ["horse ears, horse tail", 5],
    ["monkey ears, monkey tail", 5],
    ["mouse ears, mouse tail", 5],
    ["sheep ears, sheep horns", 5],
    ["squirrel ears, squirrel tail", 5],
    ["tiger ears, tiger tail", 5],
    ["wolf ears, wolf tail", 5],
    ["oni, oni horns", 5],
    ["elf, pointy ears", 5],
    ["elf, long pointy ears", 5],
    ["dark elf, pointy ears", 5],
    ["dark elf, long pointy ears", 5],
    ["fairy", 5],
    ["dragon horns, dragon tail", 5],
    ["demon horns, demon tail", 5],
    ["cow ears, cow horns", 5],
    ["angel", 5],
    ["android", 5],
    ["mermaid, scales", 5],
    ["head fins, fish tail", 5],
    ["raccoon ears, raccoon tail", 5],
    ["slime girl", 5],
    ["lamia", 5],
    ["harpy", 5],
    ["orc", 5],
    ["cyclops", 5],
    ["centaur", 5],
    ["monster", 5],
]
skinColors = [
    ["dark skin", 200],
    ["very dark skin", 200],
    ["pale skin", 200],
    ["tan", 50],
    ["black skin", 5],
    ["blue skin", 5],
    ["green skin", 5],
    ["grey skin", 5],
    ["orange skin", 5],
    ["pink skin", 5],
    ["purple skin", 5],
    ["red skin", 5],
    ["white skin", 5],
    ["yellow skin", 5],
]
eyeStyles = [
    ["heterochromia", 5],
    ["multicolored eyes", 5],
    ["no eyes", 2],
    ["ringed eyes", 5],
    ["heart-shaped pupils", 5],
    ["star-shaped pupils", 5],
    ["bags under eyes", 5],
    ["glowing eyes", 5],
    ["glowing eye", 5],
    ["bright pupils", 5],
    ["sparkling eyes", 5],
]
strangeEyeEffects = [
    ["crazy eyes", 2],
    ["empty eyes", 5],
    ["solid circle eyes", 2],
    ["solid oval eyes", 2],
    ["jitome", 5],
    ["tareme", 5],
    ["tsurime", 5],
    ["sanpaku", 5],
    ["long eyelashes", 5],
]
hairLengths = [
    ["very short hair", 5],
    ["short hair", 5],
    ["medium hair", 5],
    ["long hair", 5],
    ["very long hair", 2],
    ["absurdly long hair", 2],
    ["big hair", 5],
]
braidStyles = [
    ["braid", 5],
    ["braided bangs", 5],
    ["front braid", 5],
    ["side braid", 5],
    ["french braid", 5],
    ["crown braid", 5],
    ["single braid", 5],
    ["multiple braids", 5],
    ["braided ponytail", 5],
    ["hair bun", 5],
    ["braided bun", 5],
    ["single hair bun", 5],
    ["double bun", 5],
    ["hair rings", 5],
    ["half updo", 5],
    ["one side up", 5],
    ["two side up", 5],
    ["cone hair bun", 5],
    ["low-braided long hair", 5],
    ["low-tied long hair", 5],
    ["ponytail", 5],
    ["folded ponytail", 5],
    ["high ponytail", 5],
    ["short ponytail", 5],
    ["side ponytail", 5],
    ["split ponytail", 5],
    ["twintails", 5],
    ["low twintails", 5],
    ["short twintails", 5],
    ["uneven twintails", 5],
    ["sidecut", 5],
    ["asymmetrical hair", 5],
    ["hime cut", 5],
    ["curly hair", 5],
]
hairStyles = [
    ["drill hair", 5],
    ["twin drills", 5],
    ["hair flaps", 5],
    ["messy hair", 5],
    ["pointy hair", 5],
    ["ringlets", 5],
    ["spiked hair", 5],
    ["straight hair", 5],
    ["wavy hair", 5],
    ["blunt ends", 5],
    ["flipped hair", 5],
]
bangsStyles = [
    ["arched bangs", 5],
    ["asymmetrical bangs", 5],
    ["bangs pinned back", 5],
    ["blunt bangs", 5],
    ["crossed bangs", 5],
    ["dyed bangs", 5],
    ["hair over eyes", 5],
    ["hair over one eye", 5],
    ["long bangs", 5],
    ["parted bangs", 5],
    ["short bangs", 5],
    ["swept bangs", 5],
    ["hair between eyes", 5],
    ["hair intakes", 5],
    ["sidelocks", 5],
    ["asymmetrical sidelocks", 5],
    ["drill sidelocks", 5],
    ["single sidelock", 5],
    ["hair pulled back", 5],
    ["hair slicked back", 5],
    ["ahoge", 5],
    ["antenna hair", 5],
    ["hair spread out", 2],
    ["cowlick", 5],
]
breastSizes = [
    ["flat chest", 5],
    ["small breasts", 10],
    ["medium breasts", 10],
    ["large breasts", 5],
    ["huge breasts", 2],
    ["gigantic breasts", 1],
    ["sagging breasts", 1],
]
bodyFeatures = [
    ["forehead", 5],
    ["collarbone", 5],
    ["ribs", 5],
    ["neck", 5],
    ["narrow waist", 5],
    ["wide hips", 5],
    ["shiny skin", 5],
    ["thighs", 5],
    ["thick thighs", 5],
    ["thigh gap", 5],
    ["third eye", 3],
    ["thick eyebrows", 5],
    ["teeth", 5],
    ["stomach", 5],
    ["plump", 5],
    ["scar", 3],
    ["petite", 5],
    ["muscular", 5],
    ["mature", 5],
    ["huge ass", 1],
    ["flat ass", 1],
    ["mole under eye", 4],
    ["mole under mouth", 4],
    ["mole", 3],
    ["mole on thigh", 3],
    ["freckles", 5],
    ["curvy", 5],
    ["androgynous", 5],
    ["abs", 5],
    ["old", 5],
    ["toned", 5],
    ["fat", 1],
    ["biceps", 5],
    ["knees", 5],
    ["skinny", 5],
    ["hip bones", 5],
    ["thick arms", 5],
    ["tall", 5],
]
hatTypes = [
    ["baseball cap", 5],
    ["cabbie hat", 5],
    ["deerstalker", 5],
    ["peaked cap", 5],
    ["shako cap", 5],
    ["bicorne", 5],
    ["bowler hat", 5],
    ["cowboy hat", 5],
    ["straw hat", 5],
    ["fedora", 5],
    ["female service cap", 5],
    ["flat cap", 5],
    ["pirate hat", 5],
    ["sun hat", 5],
    ["top hat", 5],
    ["tricorne", 5],
    ["witch hat", 5],
    ["wizard hat", 5],
    ["dixie cup hat", 5],
    ["chef hat", 5],
    ["beret", 5],
    ["beanie", 5],
    ["coif", 5],
    ["fur hat", 5],
    ["nightcap", 5],
    ["nurse cap", 5],
    ["party hat", 5],
    ["sailor hat", 5],
    ["santa hat", 5],
    ["animal hat", 5],
    ["crown", 5],
    ["circlet", 5],
    ["diadem", 5],
    ["tiara", 5],
    ["aviator cap", 5],
    ["bandana", 5],
    ["bonnet", 5],
    ["head scarf", 5],
    ["jester cap", 5],
    ["frilled hat", 5],
    ["military hat", 5],
    ["police hat", 5],
    ["visor cap", 5],
    ["headpiece", 5],
    ["garrison cap", 5],
    ["head wreath", 5],
    ["flower wreath", 5],
    ["animal on head", 5],
]
hairAccessories = [
    ["hair ribbon", 5],
    ["hair bow", 5],
    ["hairband", 5],
    ["headband", 5],
    ["headdress", 5],
    ["veil", 5],
    ["hooded cloak", 5],
]
hatAccessories = [
    ["hat bow", 5],
    ["hat flower", 5],
    ["hat ornament", 5],
    ["hat ribbon", 5],
    ["hat with ears", 5],
]
dressStyles = [
    ["coat dress", 5],
    ["cocktail dress", 5],
    ["dirndl", 5],
    ["evening gown", 5],
    ["funeral dress", 5],
    ["gown", 5],
    ["nightgown", 5],
    ["pencil dress", 5],
    ["sailor dress", 5],
    ["santa dress", 5],
    ["sundress", 5],
    ["sweater dress", 5],
    ["tube dress", 5],
    ["wedding dress", 5],
    ["fur-trimmed dress", 5],
    ["armored dress", 5],
    ["backless dress", 5],
    ["collared dress", 5],
    ["frilled dress", 5],
    ["halter dress", 5],
    ["latex dress", 5],
    ["layered dress", 5],
    ["long dress", 5],
    ["off-shoulder dress", 5],
    ["pleated dress", 5],
    ["ribbed dress", 5],
    ["ribbon-trimmed dress", 5],
    ["short dress", 5],
    ["see-through dress", 5],
    ["sleeveless dress", 5],
    ["strapless dress", 5],
    ["china dress", 5],
    ["fundoshi", 5],
    ["hakama", 5],
    ["kimono", 5],
    ["yukata", 5],
    ["furisode", 5],
]
legWearTypes = [
    ["socks", 5],
    ["kneehighs", 5],
    ["over-kneehighs", 5],
    ["thighhighs", 5],
    ["pantyhose", 5],
    ["leggings", 5],
    ["leg warmers", 5],
    ["loose socks", 5],
]
detailedLegWear = [
    ["fishnet legwear", 5],
    ["bow legwear", 5],
    ["ribbed legwear", 5],
    ["seamed legwear", 5],
    ["see-through legwear", 5],
    ["shiny legwear", 5],
    ["toeless legwear", 5],
    ["fur-trimmed legwear", 5],
    ["lace-trimmed legwear", 5],
    ["uneven legwear", 5],
    ["mismatched legwear", 5],
]
topWear = [
    ["blouse", 5],
    ["frilled shirt", 5],
    ["sleeveless shirt", 5],
    ["bustier", 5],
    ["crop top", 5],
    ["camisole", 5],
    ["babydoll", 5],
    ["chemise", 5],
    ["nightgown", 5],
    ["cardigan", 5],
    ["cardigan vest", 5],
    ["coat", 5],
    ["duffel coat", 5],
    ["fur coat", 5],
    ["fur-trimmed coat", 5],
    ["long coat", 5],
    ["overcoat", 5],
    ["raincoat", 5],
    ["trench coat", 5],
    ["winter coat", 5],
    ["compression shirt", 5],
    ["halterneck", 5],
    ["criss-cross halter", 5],
    ["hoodie", 5],
    ["jacket", 5],
    ["blazer", 5],
    ["cropped jacket", 5],
    ["letterman jacket", 5],
    ["safari jacket", 5],
    ["suit jacket", 5],
    ["leather jacket", 5],
    ["poncho", 5],
    ["raglan sleeves", 5],
    ["shirt", 5],
    ["collared shirt", 5],
    ["dress shirt", 5],
    ["off-shoulder shirt", 5],
    ["sleeveless shirt", 5],
    ["striped shirt", 5],
    ["t-shirt", 5],
    ["shrug (clothing)", 5],
    ["surcoat", 5],
    ["sweater", 5],
    ["turtleneck", 5],
    ["sleeveless turtleneck", 5],
    ["ribbed sweater", 5],
    ["aran sweater", 5],
    ["argyle sweater", 5],
    ["virgin killer sweater", 5],
    ["tabard", 5],
    ["tailcoat", 5],
    ["tank top", 5],
    ["tube top", 5],
    ["bandeau", 5],
    ["underbust", 5],
    ["vest", 5],
    ["sweater vest", 5],
    ["waistcoat", 5],
    ["sarashi", 5],
    ["tunic", 5],
    ["front-tie top", 5],
    ["breast curtains", 5],
    ["pasties", 1],
    ["heart pasties", 1],
]
bottomWear = [
    ["bloomers", 5],
    ["buruma", 5],
    ["chaps", 5],
    ["kilt", 5],
    ["pants", 5],
    ["tight pants", 5],
    ["baggy pants", 5],
    ["bell-bottoms", 5],
    ["capri pants", 5],
    ["detached pants", 5],
    ["jeans", 5],
    ["lowleg pants", 5],
    ["pants rolled up", 5],
    ["yoga pants", 5],
    ["pelvic curtain", 5],
    ["petticoat", 5],
    ["shorts", 5],
    ["bike shorts", 5],
    ["denim shorts", 5],
    ["dolphin shorts", 5],
    ["gym shorts", 5],
    ["lowleg shorts", 5],
    ["micro shorts", 5],
    ["short shorts", 5],
    ["suspender shorts", 5],
    ["shorts under skirt", 5],
    ["skirt", 5],
    ["bubble skirt", 5],
    ["high-waist skirt", 5],
    ["long skirt", 5],
    ["lowleg skirt", 5],
    ["microskirt", 5],
    ["miniskirt", 5],
    ["overall skirt", 5],
    ["plaid skirt", 5],
    ["pleated skirt", 5],
    ["suspender skirt", 5],
    ["showgirl skirt", 5],
    ["sweatpants", 5],
]
bootTypes = [
    ["boots", 5],
    ["ankle boots", 5],
    ["armored boots", 5],
    ["cowboy boots", 5],
    ["knee boots", 5],
    ["high heel boots", 5],
    ["lace-up boots", 5],
    ["rubber boots", 5],
    ["thigh boots", 5],
    ["cross-laced footwear", 5],
    ["dress shoes", 5],
    ["flats", 5],
    ["high heels", 5],
    ["loafers", 5],
    ["mary janes", 5],
    ["platform footwear", 5],
    ["pointy footwear", 5],
    ["pumps", 5],
    ["sandals", 5],
    ["flip-flops", 5],
    ["geta", 5],
    ["gladiator sandals", 5],
    ["okobo", 5],
    ["zouri", 5],
    ["slippers", 5],
    ["animal slippers", 5],
    ["ballet slippers", 5],
    ["crocs", 5],
    ["uwabaki", 5],
    ["sneakers", 5],
    ["high tops", 5],
    ["converse", 5],
    ["toeless footwear", 5],
    ["wedge heels", 5],
]
clothingArmor = [
    ["armor", 5],
    ["full armor", 5],
    ["power armor", 5],
    ["armored dress", 5],
    ["bikini armor", 5],
    ["band uniform", 5],
    ["cassock", 5],
    ["cheerleader", 5],
    ["ghost costume", 5],
    ["business suit", 5],
    ["pant suit", 5],
    ["skirt suit", 5],
    ["tuxedo", 5],
    ["gym uniform", 5],
    ["habit", 5],
    ["harem outfit", 5],
    ["hazmat suit", 5],
    ["animal costume", 5],
    ["maid", 5],
    ["unconventional maid", 5],
    ["miko", 5],
    ["military uniform", 5],
    ["overalls", 5],
    ["pajamas", 5],
    ["pilot suit", 5],
    ["sailor", 5],
    ["santa costume", 5],
    ["school uniform", 5],
    ["serafuku", 5],
    ["track suit", 5],
    ["tutu", 5],
    ["waitress", 5],
    ["cowboy western", 5],
    ["magical girl", 5],
    ["lab coat", 5],
    ["idol", 5],
    ["police", 5],
    ["race queen", 5],
    ["bride", 5],
    ["knight", 5],
    ["tomboy", 5],
    ["soccer uniform", 5],
    ["employee uniform", 5],
    ["dancer", 5],
    ["spacesuit", 5],
    ["idol", 5],
    ["gyaru", 5],
    ["kogal", 5],
    ["soldier", 5],
    ["pirate", 5],
    ["princess", 5],
    ["samurai", 5],
    ["priest", 5],
    ["nun", 5],
]
bodySuits = [
    ["bikesuit", 5],
    ["racing suit", 5],
    ["bodysuit", 5],
    ["jumpsuit", 5],
    ["short jumpsuit", 5],
    ["leotard", 5],
    ["strapless leotard", 5],
    ["thong leotard", 5],
    ["robe", 5],
    ["unitard", 5],
    ["springsuit", 5],
]
swimwear = [
    ["swimsuit", 5],
    ["one-piece swimsuit", 5],
    ["casual one-piece swimsuit", 5],
    ["competition swimsuit", 5],
    ["slingshot swimsuit", 5],
    ["square bikini", 5],
    ["school swimsuit", 5],
    ["bikini", 5],
    ["string bikini", 5],
    ["micro bikini", 5],
    ["lowleg bikini", 5],
    ["thong bikini", 5],
    ["sports bikini", 5],
    ["swim briefs", 5],
    ["rash guard", 5],
    ["wetsuit", 5],
    ["front-tie bikini top", 5],
    ["o-ring bikini", 5],
    ["strapless bikini", 5],
    ["maid bikini", 5],
    ["swim trunks", 5],
]
accessories = [
    ["apron", 5],
    ["cape", 5],
    ["capelet", 5],
    ["hood", 5],
    ["bodystocking", 5],
    ["ascot", 5],
    ["bowtie", 5],
    ["choker", 5],
    ["collar", 5],
    ["epaulettes", 5],
    ["feather boa", 5],
    ["lapels", 5],
    ["neck ruff", 5],
    ["neckerchief", 5],
    ["necklace", 5],
    ["necktie", 5],
    ["neck ribbon", 5],
    ["scarf", 5],
    ["shawl", 5],
    ["anklet", 5],
    ["arm belt", 5],
    ["armband", 5],
    ["armlet", 5],
    ["bracelet", 5],
    ["bangle", 5],
    ["spiked bracelet", 5],
    ["bridal gauntlets", 5],
    ["detached sleeves", 5],
    ["arm warmers", 5],
    ["gloves", 5],
    ["fingerless gloves", 5],
    ["elbow gloves", 5],
    ["half gloves", 5],
    ["mittens", 5],
    ["leg belt", 5],
    ["ring", 5],
    ["thighlet", 5],
    ["wide sleeves", 5],
    ["wristband", 5],
    ["wrist cuffs", 5],
    ["cuffs", 5],
    ["wrist scrunchie", 5],
    ["badge", 5],
    ["belly chain", 5],
    ["belt", 5],
    ["brooch", 5],
    ["buttons", 5],
    ["collar chain", 5],
    ["corsage", 5],
    ["cuff links", 5],
    ["pentacle", 5],
    ["sarong", 5],
    ["sash", 5],
    ["suspenders", 5],
    ["tassel", 5],
    ["clothing cutout", 5],
    ["flower trim", 5],
    ["frills", 5],
    ["gold trim", 5],
    ["lace trim", 5],
    ["ribbon trim", 5],
    ["see-through", 5],
    ["silver trim", 5],
    ["torn clothes", 5],
    ["earrings", 5],
    ["hoop earrings", 5],
    ["stud earrings", 5],
    ["earclip", 5],
    ["glasses", 5],
    ["monocle", 5],
    ["hair ornament", 5],
    ["hair beads", 5],
    ["hair bobbles", 5],
    ["hairclip", 5],
    ["hairpin", 5],
    ["hair scrunchie", 5],
    ["hair stick", 5],
    ["mask", 5],
    ["surgical mask", 5],
    ["sleeves pushed up", 5],
    ["sleeves rolled up", 5],
    ["short sleeves", 5],
    ["long sleeves", 5],
    ["sleeves past wrists", 5],
    ["sleeves past fingers", 5],
    ["sleeves past elbows", 5],
    ["puffy sleeves", 5],
    ["sleeveless", 5],
    ["goggles", 5],
    ["sunglasses", 5],
    ["coke-bottle glasses", 5],
    ["opaque glasses", 5],
    ["safety glasses", 5],
    ["ski goggles", 5],
    ["bespectacled", 5],
    ["ear piercing", 5],
    ["eyebrow piercing", 5],
    ["lip piercing", 5],
    ["nose piercing", 5],
    ["tongue piercing", 5],
    ["navel piercing", 5],
    ["zipper", 5],
    ["zettai ryouiki", 5],
    ["wristwatch", 5],
    ["x hair ornament", 5],
    ["wing collar", 5],
    ["whisker markings", 5],
    ["wet", 5],
    ["weapon", 5],
    ["wand", 5],
    ["waist apron", 5],
    ["veins", 5],
    ["vambraces", 5],
    ["valentine", 5],
    ["underboob", 5],
    ["umbrella", 5],
    ["under-rim eyewear", 5],
    ["unbuttoned", 5],
    ["tray", 5],
    ["toenail polish", 5],
    ["tentacles", 5],
    ["tattoo", 5],
    ["tanlines", 5],
    ["swimsuit under clothes", 5],
    ["sweat", 5],
    ["striped", 5],
    ["strap slip", 5],
    ["star print", 5],
    ["spikes", 5],
    ["sideboob", 5],
    ["side slit", 5],
    ["shoulder armor", 5],
    ["shoulder bag", 5],
    ["shoulder cutout", 5],
    ["shoulder tattoo", 5],
    ["shirt tucked in", 5],
    ["shiny clothes", 5],
    ["sharp teeth", 5],
    ["sharp fingernails", 5],
    ["saliva", 5],
    ["pouch", 5],
    ["polka dot", 5],
    ["pom pom (clothes)", 5],
    ["pocket", 5],
    ["revealing clothes", 5],
    ["ribbon", 5],
    ["ribbon choker", 5],
    ["randoseru", 5],
    ["semi-rimless eyewear", 5],
    ["scrunchie", 5],
    ["school bag", 5],
    ["plaid", 5],
    ["pendant", 5],
    ["pauldrons", 5],
    ["partially unbuttoned", 5],
    ["paw gloves", 5],
    ["open clothes", 5],
    ["off shoulder", 5],
    ["o-ring top", 5],
    ["neck bell", 5],
    ["navel cutout", 5],
    ["mustache", 5],
    ["wings", 5],
    ["low wings", 5],
    ["lipstick", 5],
    ["leg ribbon", 5],
    ["leash", 5],
    ["lace", 5],
    ["knee pads", 5],
    ["kemonomimi mode", 5],
    ["juliet sleeves", 5],
    ["joints", 5],
    ["jewelry", 5],
    ["jacket on shoulders", 5],
    ["impossible clothes", 5],
    ["ice wings", 5],
    ["horns", 5],
    ["curled horns", 5],
    ["highleg", 5],
    ["high collar", 5],
    ["helmet", 5],
    ["mouth mask", 5],
    ["midriff peek", 5],
    ["midriff", 5],
    ["mechanical arms", 5],
    ["mask on head", 5],
    ["makeup", 5],
    ["long fingernails", 5],
    ["helmet", 5],
    ["halo", 5],
    ["hair tubes", 5],
    ["gauntlets", 5],
    ["garter straps", 5],
    ["fur trim", 5],
    ["floating hair", 5],
    ["fins", 5],
    ["fangs", 5],
    ["fang out", 5],
    ["facial mark", 5],
    ["facial hair", 5],
    ["eyeshadow", 5],
    ["eyes visible through hair", 5],
    ["eyepatch", 5],
    ["eyeliner", 5],
    ["eyelashes", 5],
    ["eyebrows", 5],
    ["eyewear on head", 5],
    ["earmuffs", 5],
    ["covered navel", 5],
    ["corset", 5],
    ["contemporary", 5],
    ["colored eyelashes", 5],
    ["cleavage cutout", 5],
    ["cleavage", 5],
    ["claws", 5],
    ["checkered clothes", 5],
    ["center opening", 5],
    ["center frills", 5],
    ["breasts apart", 5],
    ["breastplate", 5],
    ["breast pocket", 5],
    ["bracer", 5],
    ["blood on clothes", 2],
    ["blood on face", 2],
    ["blindfold", 5],
    ["bare shoulders", 5],
    ["bare arms", 5],
    ["bare legs", 5],
    ["bandaid on face", 5],
    ["bandaid", 5],
    ["bandages", 5],
    ["bandaged leg", 5],
    ["bandaged arm", 5],
    ["backpack", 5],
    ["backless outfit", 5],
    ["back bow", 5],
    ["ass visible through thighs", 5],
    ["ass focus", 5],
    ["armpits", 5],
    ["armpit crease", 5],
    ["arm tattoo", 5],
    ["animal print", 5],
    ["clothes around waist", 5],
    ["headphones around neck", 5],
    ["oversized clothes", 5],
    ["manly", 5],
    ["greaves", 5],
    ["one-eyed", 5],
    ["fur-trimmed sleeves", 5],
    ["polka dot bow", 5],
    ["harness", 5],
    ["forehead jewel", 5],
    ["single bare shoulder", 5],
    ["spiked collar", 5],
    ["striped necktie", 5],
    ["arm guards", 5],
    ["undershirt", 5],
    ["latex", 5],
    ["bandaid on leg", 5],
    ["bead necklace", 5],
    ["dirty", 5],
    ["motorcycle", 5],
    ["giantess", 5],
    ["cyborg", 5],
    ["bruise", 5],
    ["waist cape", 5],
    ["extra arms", 5],
    ["taut shirt", 5],
    ["chest jewel", 5],
    ["v-neck", 5],
    ["plaid scarf", 5],
    ["prosthesis", 5],
    ["single mechanical arm", 5],
    ["blood on hands", 2],
    ["bandaid on nose", 5],
    ["robot joints", 5],
    ["zombie", 5],
    ["tail ribbon", 5],
    ["tomboy", 5],
    ["panty peek", 5],
    ["leg tattoo", 5],
    ["lanyard", 5],
    ["bra visible through clothes", 5],
    ["amputee", 5],
    ["bra strap", 5],
    ["money", 5],
    ["revolver", 5],
    ["pearl necklace", 5],
    ["dimples of venus", 5],
    ["coat on shoulders", 5],
    ["chest harness", 5],
    ["slime (substance)", 5],
    ["partially unzipped", 5],
    ["bodypaint", 5],
    ["metal collar", 5],
    ["loose necktie", 5],
    ["clover", 5],
    ["body markings", 5],
    ["mechanical wings", 5],
    ["leaf print", 5],
    ["pentagram", 5],
    ["neon trim", 5],
    ["prosthetic arm", 5],
    ["bandage over one eye", 5],
    ["mascara", 5],
    ["cat ear headphones", 5],
    ["cuts", 5],
    ["jacket around waist", 5],
    ["bleeding", 5],
    ["rectangular eyewear", 5],
    ["chain necklace", 5],
    ["medal", 5],
    ["tie clip", 5],
    ["paw shoes", 5],
    ["feather trim", 5],
    ["gold chain", 5],
    ["mechanical parts", 5],
    ["seamed legwear", 5],
    ["mechanical legs", 5],
    ["eye mask", 5],
    ["scratches", 5],
    ["cross scar", 5],
    ["tusks", 5],
    ["dragon print", 5],
    ["sun symbol", 5],
    ["uneven sleeves", 5],
    ["energy wings", 5],
    ["cat print", 5],
    ["sweatband", 5],
    ["sweater around waist", 5],
    ["single vertical stripe", 5],
    ["glowing sword", 5],
    ["fanny pack", 5],
    ["blood stain", 2],
    ["single pauldron", 5],
    ["panty straps", 5],
    ["energy ball", 5],
    ["scepter", 5],
    ["cherry blossom print", 5],
    ["insect wings", 5],
    ["constellation print", 5],
    ["utility belt", 5],
    ["prosthetic leg", 5],
    ["very sweaty", 5],
    ["scales", 5],
    ["fake animal ears", 5],
]
facialExpressions = [
    ["wince", 5],
    ["wide-eyed", 5],
    ["tears", 5],
    ["triangle mouth", 5],
    ["trembling", 5],
    ["tongue out", 5],
    ["tearing up", 5],
    ["sweatdrop", 5],
    ["surprised", 5],
    ["spoken heart", 5],
    ["spoken question mark", 5],
    ["spoken heart", 5],
    ["spoken ellipsis", 5],
    ["smug", 5],
    ["smirk", 5],
    ["smile", 5],
    ["serious", 5],
    ["shaded face", 5],
    ["pout", 5],
    ["parted lips", 5],
    ["o_o", 5],
    ["notice lines", 5],
    ["nose blush", 5],
    ["naughty face", 5],
    ["light smile", 5],
    ["light blush", 5],
    ["licking lips", 5],
    ["laughing", 5],
    ["heavy breathing", 5],
    ["happy", 5],
    ["half-closed eyes", 5],
    ["grin", 5],
    ["frown", 5],
    ["flying sweatdrops", 5],
    ["expressionless", 5],
    ["evil smile", 5],
    ["embarrassed", 5],
    ["drunk", 5],
    ["crying with eyes open", 5],
    ["crying", 5],
    ["closed eyes", 5],
    ["clenched teeth", 5],
    ["chestnut mouth", 5],
    ["blush stickers", 5],
    ["blush", 5],
    ["angry", 5],
    ["anger vein", 5],
    ["ahegao", 1],
    ["^_^", 5],
    ["@_@", 5],
    ["?", 5],
    [">:)", 5],
    ["=_=", 5],
    [";d", 5],
    [";)", 5],
    [":t", 5],
    [":q", 5],
    [":p", 5],
    [":o", 5],
    [":d", 5],
    [":>", 5],
    [":<", 5],
    [":3", 5],
    ["...", 5],
    ["+_+", 5],
    ["+++", 5],
    ["!?", 5],
    ["!", 5],
    ["annoyed", 5],
    ["spoken exclamation mark", 5],
    ["sad", 5],
    [":/", 5],
    ["!!", 5],
    ["nervous", 5],
    ["0_0", 5],
    [";o", 5],
    ["seductive smile", 5],
    ["zzz", 5],
    ["torogao", 5],
    ["d:", 5],
    ["sleepy", 5],
    ["ear blush", 5],
    ["nervous sweating", 5],
    ["=3", 5],
    ["spoken musical note", 5],
    ["glaring", 5],
    [";p", 5],
    ["yandere", 5],
    ["shy", 5],
    ["streaming tears", 5],
    ["spoken blush", 5],
    [">:(", 5],
    ["evil grin", 5],
    ["nervous smile", 5],
    [";q", 5],
    ["spoken squiggle", 5],
    ["spoken interrobang", 5],
    ["thinking", 5],
    ["puckered lips", 5],
    ["screaming", 5],
    ["spoken anger vein", 5],
    ["dot mouth", 5],
    ["grimace", 5],
    [";3", 5],
    ["confused", 5],
    ["worried", 5],
    ["u_u", 5],
    ["raised eyebrows", 5],
]
years = [
    ["year 2005", 5],
    ["year 2006", 5],
    ["year 2007", 5],
    ["year 2008", 5],
    ["year 2009", 5],
    ["year 2010", 5],
    ["year 2011", 5],
    ["year 2012", 5],
    ["year 2013", 5],
    ["year 2014", 5],
    ["year 2015", 5],
    ["year 2016", 5],
    ["year 2017", 5],
    ["year 2018", 5],
    ["year 2018", 5],
    ["year 2019", 5],
    ["year 2020", 5],
    ["year 2021", 5],
    ["year 2022", 5],
    ["year 2023", 5],
]
environmentElements = [
    ["wooden floor", 5],
    ["window", 5],
    ["wine glass", 5],
    ["water drop", 5],
    ["water", 5],
    ["wall", 5],
    ["underwater", 5],
    ["torii", 5],
    ["tatami", 5],
    ["steam", 5],
    ["starry sky", 5],
    ["stairs", 5],
    ["space", 5],
    ["snow", 5],
    ["snowing", 5],
    ["smoke", 5],
    ["sky", 5],
    ["shadow", 5],
    ["shade", 5],
    ["sand", 5],
    ["road", 5],
    ["rigging", 5],
    ["reflection", 5],
    ["rain", 5],
    ["railing", 5],
    ["pool", 5],
    ["palm tree", 5],
    ["outdoors", 5],
    ["onsen", 5],
    ["ocean", 5],
    ["night sky", 5],
    ["night", 5],
    ["nature", 5],
    ["moon", 5],
    ["mountain", 5],
    ["indoors", 5],
    ["horizon", 5],
    ["grass", 5],
    ["full moon", 5],
    ["frog", 5],
    ["forest", 5],
    ["field", 5],
    ["fence", 5],
    ["desk", 5],
    ["day", 5],
    ["curtains", 5],
    ["couch", 5],
    ["cloudy sky", 5],
    ["cloud", 5],
    ["classroom", 5],
    ["cityscape", 5],
    ["city", 5],
    ["car", 5],
    ["bush", 5],
    ["building", 5],
    ["bookshelf", 5],
    ["bedroom", 5],
    ["bed", 5],
    ["beach", 5],
    ["bath", 5],
    ["vines", 5],
    ["bamboo", 5],
    ["house", 5],
    ["ruins", 5],
    ["crescent moon", 5],
    ["sliding doors", 5],
    ["brick wall", 5],
    ["east asian architecture", 5],
    ["futon", 5],
    ["bridge", 5],
    ["planet", 5],
    ["shelf", 5],
    ["bare tree", 5],
    ["street", 5],
    ["river", 5],
    ["castle", 5],
    ["flower field", 5],
    ["skyscraper", 5],
    ["utility pole", 5],
    ["train interior", 5],
    ["evening", 5],
    ["mountainous horizon", 5],
    ["waves", 5],
    ["crowd", 5],
    ["kitchen", 5],
    ["tower", 5],
    ["waterfall", 5],
    ["library", 5],
    ["puddle", 5],
    ["shop", 5],
    ["lake", 5],
    ["fog", 5],
    ["shrine", 5],
    ["red moon", 5],
    ["rooftop", 5],
    ["shore", 5],
    ["floor", 5],
    ["contrail", 5],
    ["shooting star", 5],
    ["ceiling", 5],
    ["city lights", 5],
    ["bamboo forest", 5],
    ["hallway", 5],
    ["moonlight", 5],
    ["locker room", 5],
    ["dusk", 5],
    ["sink", 5],
    ["tombstone", 5],
    ["hill", 5],
    ["sunrise", 5],
    ["restaurant", 5],
    ["moss", 5],
    ["church", 5],
    ["town", 5],
    ["cave", 5],
    ["festival", 5],
    ["veranda", 5],
    ["reflective floor", 5],
    ["alley", 5],
    ["pond", 5],
    ["tree", 5],
    ["overgrown", 5],
]
smallObjects = [
    ["strawberry", 5],
    ["teddy bear", 5],
    ["teacup", 5],
    ["teapot", 5],
    ["spoon", 5],
    ["smartphone", 5],
    ["skull", 5],
    ["shield", 5],
    ["sheath", 5],
    ["school desk", 5],
    ["scythe", 5],
    ["sack", 5],
    ["rose", 5],
    ["rope", 5],
    ["rock", 5],
    ["rifle", 5],
    ["pumpkin", 5],
    ["potted plant", 5],
    ["popsicle", 5],
    ["polearm", 5],
    ["pocky", 5],
    ["plate", 5],
    ["plant", 5],
    ["pen", 5],
    ["phone", 5],
    ["peach", 5],
    ["parasol", 5],
    ["open book", 5],
    ["ofuda", 5],
    ["mug", 5],
    ["motor vehicle", 5],
    ["mecha", 5],
    ["machinery", 5],
    ["lollipop", 5],
    ["leaf", 5],
    ["lantern", 5],
    ["lamp", 5],
    ["knife", 5],
    ["key", 5],
    ["katana", 5],
    ["jack-o'-lantern", 5],
    ["instrument", 5],
    ["innertube", 5],
    ["id card", 5],
    ["ice cream", 5],
    ["hibiscus", 5],
    ["headset", 5],
    ["headphones", 5],
    ["handgun", 5],
    ["handbag", 5],
    ["hand fan", 5],
    ["gun", 5],
    ["guitar", 5],
    ["gift", 5],
    ["gift box", 5],
    ["ghost", 5],
    ["gem", 5],
    ["fruit", 5],
    ["fork", 5],
    ["food", 5],
    ["folding fan", 5],
    ["flower", 5],
    ["fish", 5],
    ["doll", 5],
    ["disposable cup", 5],
    ["dagger", 5],
    ["cup", 5],
    ["cross", 5],
    ["controller", 5],
    ["computer", 5],
    ["cigarette", 5],
    ["chopsticks", 5],
    ["chocolate", 5],
    ["chair", 5],
    ["chain", 5],
    ["cellphone", 5],
    ["carrot", 5],
    ["cannon", 5],
    ["candy", 5],
    ["candle", 5],
    ["can", 5],
    ["camera", 5],
    ["cake", 5],
    ["butterfly", 5],
    ["bucket", 5],
    ["broom", 5],
    ["branch", 5],
    ["box", 5],
    ["bowl", 5],
    ["bouquet", 5],
    ["bottle", 5],
    ["book", 5],
    ["blanket", 5],
    ["bird", 5],
    ["bench", 5],
    ["bell", 5],
    ["bed sheet", 5],
    ["beads", 5],
    ["beachball", 5],
    ["basket", 5],
    ["balloon", 5],
    ["ball", 5],
    ["axe", 5],
    ["assault rifle", 5],
    ["apple", 5],
    ["alcohol", 5],
    ["paintbrush", 5],
    ["tea", 5],
    ["black cat", 5],
    ["maple leaf", 5],
    ["mushroom", 5],
    ["television", 5],
    ["handcuffs", 5],
    ["doughnut", 5],
    ["water bottle", 5],
    ["bread", 5],
    ["pink rose", 5],
    ["monitor", 5],
    ["handheld game console", 5],
    ["huge weapon", 5],
    ["earphones", 5],
    ["tank", 5],
    ["stool", 5],
    ["smoking pipe", 5],
    ["cookie", 5],
    ["chalkboard", 5],
    ["coin", 5],
    ["syringe", 5],
    ["christmas tree", 5],
    ["rice", 5],
    ["bathtub", 5],
    ["beer", 5],
    ["lamppost", 5],
    ["egg", 5],
    ["cherry", 5],
    ["cushion", 5],
    ["scissors", 5],
    ["horse", 5],
    ["shell", 5],
    ["sake", 5],
    ["burger", 5],
    ["coffee", 5],
    ["clipboard", 5],
    ["skeleton", 5],
    ["electric guitar", 5],
    ["cardboard box", 5],
    ["lily (flower)", 5],
    ["pillar", 5],
    ["book stack", 5],
    ["wine", 5],
    ["mouse", 5],
    ["laptop", 5],
    ["kotatsu", 5],
    ["shopping bag", 5],
    ["whip", 5],
    ["dango", 5],
    ["grapes", 5],
    ["water gun", 5],
    ["paper lantern", 5],
    ["vase", 5],
    ["whistle", 5],
    ["noodles", 5],
    ["microphone stand", 5],
    ["bicycle", 5],
    ["notebook", 5],
    ["hydrangea", 5],
    ["suitcase", 5],
    ["ship", 5],
    ["bone", 5],
    ["ice cream cone", 5],
    ["elbow pads", 5],
    ["heart-shaped chocolate", 5],
    ["lance", 5],
    ["cane", 5],
    ["ladle", 5],
    ["orange (fruit)", 5],
    ["spring onion", 5],
    ["statue", 5],
    ["locker", 5],
    ["gears", 5],
    ["crab", 5],
    ["wine bottle", 5],
    ["gourd", 5],
    ["starfish", 5],
    ["coffee mug", 5],
    ["machine gun", 5],
    ["trident", 5],
    ["lock", 5],
    ["crow", 5],
    ["boat", 5],
    ["road sign", 5],
    ["stick", 5],
    ["armchair", 5],
    ["frilled pillow", 5],
    ["tissue box", 5],
    ["jar", 5],
    ["mandarin orange", 5],
    ["keyboard (computer)", 5],
    ["thorns", 5],
    ["office chair", 5],
    ["scope", 5],
    ["pot", 5],
    ["pole", 5],
    ["food print", 5],
    ["test tube", 5],
    ["spider web", 5],
    ["rapier", 5],
    ["envelope", 5],
    ["banana", 5],
    ["lemon", 5],
    ["shotgun", 5],
    ["energy sword", 5],
    ["pizza", 5],
    ["digital media player", 5],
    ["tomato", 5],
    ["rubber duck", 5],
    ["candy apple", 5],
    ["baozi", 5],
    ["lily pad", 5],
    ["pancake", 5],
    ["soda can", 5],
    ["vegetable", 5],
    ["trash can", 5],
    ["frying pan", 5],
    ["lotus", 5],
    ["four-leaf clover", 5],
    ["plum blossoms", 5],
    ["electric fan", 5],
    ["puppet", 5],
    ["ramen", 5],
    ["bento", 5],
    ["candy cane", 5],
    ["stethoscope", 5],
    ["seashell", 5],
    ["plastic bag", 5],
    ["bass guitar", 5],
    ["flower pot", 5],
    ["pudding", 5],
    ["flask", 5],
    ["soccer ball", 5],
    ["duffel bag", 5],
    ["cigar", 5],
    ["beach towel", 5],
    ["shaved ice", 5],
    ["mallet", 5],
    ["turtle shell", 5],
    ["glowstick", 5],
    ["coffee cup", 5],
    ["drumsticks", 5],
    ["jellyfish", 5],
    ["volleyball", 5],
    ["sweets", 5],
    ["swirl lollipop", 5],
    ["pastry", 5],
    ["omelet", 5],
    ["curry", 5],
    ["milk bottle", 5],
    ["dessert", 5],
    ["black rose", 5],
    ["satchel", 5],
    ["torch", 5],
    ["transparent umbrella", 5],
    ["surfboard", 5],
    ["prayer beads", 5],
    ["potato chips", 5],
    ["racket", 5],
    ["turtle", 5],
    ["briefcase", 5],
    ["baseball", 5],
    ["wooden bucket", 5],
    ["crepe", 5],
    ["barrel", 5],
    ["ramune", 5],
    ["tulip", 5],
    ["cat teaser", 5],
    ["baseball mitt", 5],
    ["desk lamp", 5],
]
posesAndActions = [
    ["waving", 5],
    ["wariza", 5],
    ["walking", 5],
    ["wading", 5],
    ["w", 5],
    ["top-down bottom-up", 5],
    ["thought bubble", 5],
    ["talking", 5],
    ["stretching", 5],
    ["straddling", 5],
    ["standing on one leg", 5],
    ["standing", 5],
    ["spread legs", 5],
    ["spread arms", 5],
    ["skirt hold", 5],
    ["sitting", 5],
    ["shirt lift", 5],
    ["selfie", 5],
    ["salute", 5],
    ["riding", 5],
    ["restrained", 5],
    ["reading", 5],
    ["reaching towards viewer", 5],
    ["reaching", 5],
    ["pulled by self", 5],
    ["pose", 5],
    ["peace sign", 5],
    ["paw pose", 5],
    ["own hands together", 5],
    ["own hands clasped", 5],
    ["outstretched hand", 5],
    ["outstretched arms", 5],
    ["open hand", 5],
    ["on back", 5],
    ["on bed", 5],
    ["on chair", 5],
    ["on couch", 5],
    ["on floor", 5],
    ["on one knee", 5],
    ["on side", 5],
    ["on stomach", 5],
    ["lying", 5],
    ["looking up", 5],
    ["looking to the side", 5],
    ["looking down", 5],
    ["looking back", 5],
    ["looking away", 5],
    ["looking at viewer", 5],
    ["looking ahead", 5],
    ["looking afar", 5],
    ["lifted by self", 5],
    ["licking", 5],
    ["legs up", 5],
    ["legs together", 5],
    ["legs apart", 5],
    ["leg up", 5],
    ["leg lift", 5],
    ["leaning forward", 5],
    ["leaning back", 5],
    ["knees up", 5],
    ["knees together feet apart", 5],
    ["kneeling", 5],
    ["jumping", 5],
    ["indian style", 5],
    ["index finger raised", 5],
    ["hugging own legs", 5],
    ["hugging object", 5],
    ["heart hands", 5],
    ["headpat", 5],
    ["hands up", 5],
    ["hands on own hips", 5],
    ["hands on own face", 5],
    ["hands on own chest", 5],
    ["hands in pockets", 5],
    ["hand up", 5],
    ["hand to own mouth", 5],
    ["hand on own hip", 5],
    ["hand on own head", 5],
    ["hand on own chin", 5],
    ["hand on own chest", 5],
    ["hand on own cheek", 5],
    ["hand in pocket", 5],
    ["hand between legs", 5],
    ["finger to mouth", 5],
    ["fighting stance", 5],
    ["facing viewer", 5],
    ["facing away", 5],
    ["eating", 5],
    ["drinking", 5],
    ["double peace", 5],
    ["dancing", 5],
    ["crossed legs", 5],
    ["crossed arms", 5],
    ["covering mouth", 5],
    ["covering breasts", 5],
    ["covering", 5],
    ["contrapposto", 5],
    ["clothes pull", 5],
    ["clenched hands", 5],
    ["clenched hand", 5],
    ["claw pose", 5],
    ["carrying", 5],
    ["breasts squeezed together", 5],
    ["bent over", 5],
    ["arms up", 5],
    ["arms behind head", 5],
    ["arms behind back", 5],
    ["arms at sides", 5],
    ["arm up", 5],
    ["arm support", 5],
    ["arm grab", 5],
    ["arm behind head", 5],
    ["arm behind back", 5],
    ["arm at side", 5],
    ["arched back", 5],
    ["all fours", 5],
    ["against wall", 5],
    ["adjusting hair", 5],
    ["adjusting eyewear", 5],
    ["arm under breasts", 5],
    ["holding hair", 5],
    ["on ground", 5],
    ["pigeon-toed", 5],
    ["thumbs up", 5],
    ["kicking", 5],
    ["invisible chair", 5],
    ["hand on own thigh", 5],
    ["tiptoes", 5],
    ["singing", 5],
    ["falling", 5],
    ["hand on own knee", 5],
    ["holding gift", 5],
    ["playing instrument", 5],
    ["holding stuffed toy", 5],
    ["pointing at viewer", 5],
    ["broom riding", 5],
    ["leaning to the side", 5],
    ["tying hair", 5],
    ["shouting", 5],
    ["reclining", 5],
    ["pillow hug", 5],
    ["punching", 5],
    ["yawning", 5],
    ["\\m/", 5],
    ["hand on own stomach", 5],
    ["hands on own cheeks", 5],
    ["hand on own ass", 5],
    ["covering face", 5],
    ["firing", 5],
    ["strap pull", 5],
    ["shushing", 5],
    ["breast suppress", 5],
    ["peeking out", 5],
    ["squatting", 5],
    ["feet up", 5],
    ["open hands", 5],
    ["waking up", 5],
    ["hands on own knees", 5],
    ["breast lift", 5],
    ["hands in hair", 5],
    ["peace sign, v over eye", 5],
    ["pointing at self", 5],
    ["pointing up", 5],
    ["against glass", 5],
    ["holding own arm", 5],
    ["elbow rest", 5],
    ["steepled fingers", 5],
    ["hand on own arm", 5],
    ["hair tucking", 5],
    ["staring", 5],
    ["fingers together", 5],
    ["arms under breasts", 5],
    ["clothes grab", 5],
    ["exercise", 5],
    ["shirt tug", 5],
    ["finger to cheek", 5],
    ["covering own eyes", 5],
    ["come hither", 5],
    ["rubbing eyes", 5],
    ["praying", 5],
    ["zombie pose", 5],
    ["holding sign", 5],
    ["looking at phone", 5],
    ["fleeing", 5],
    ["ok sign", 5],
    ["playing with own hair", 5],
    ["hands on lap", 5],
    ["finger to own chin", 5],
    ["hands on own thighs", 5],
    ["confession", 5],
    ["wiping tears", 5],
    ["sleeping", 5],
]
visualEffects = [
    ["sparkle", 5],
    ["snowflakes", 5],
    ["petals", 5],
    ["paw print", 5],
    ["musical note", 5],
    ["motion lines", 5],
    ["magic", 5],
    ["light rays", 5],
    ["light particles", 5],
    ["lens flare", 5],
    ["ice", 5],
    ["glowing", 5],
    ["glint", 5],
    ["fire", 5],
    ["fantasy", 5],
    ["falling petals", 5],
    ["emphasis lines", 5],
    ["electricity", 5],
    ["eighth note", 5],
    ["depth of field", 5],
    ["crystal", 5],
    ["crescent", 5],
    ["confetti", 5],
    ["chromatic aberration", 5],
    ["christmas", 5],
    ["chibi", 5],
    ["cherry blossoms", 5],
    ["bubble", 5],
    ["blurry background", 5],
    ["blurry foreground", 5],
    ["autumn leaves", 5],
    ["air bubble", 5],
    ["aura", 5],
    ["halftone", 5],
    ["explosion", 5],
    ["summer", 5],
    ["sunbeam", 5],
    ["magic circle", 5],
    ["fireworks", 5],
    ["winter", 5],
    ["partially colored", 5],
    ["ripples", 5],
    ["rainbow", 5],
    ["sepia", 5],
    ["blood splatter", 2],
    ["autumn", 5],
    ["spring (season)", 5],
    ["rose petals", 5],
    ["danmaku", 5],
    ["shiny", 5],
    ["lightning", 5],
    ["blue fire", 5],
    ["falling leaves", 5],
    ["muted color", 5],
    ["soap bubbles", 5],
    ["horror (theme)", 5],
    ["colorful", 5],
    ["viewfinder", 5],
    ["constellation", 5],
    ["egyptian", 5],
    ["surreal", 5],
    ["darkness", 5],
    ["paint splatter", 5],
    ["lolita fashion", 5],
    ["bloom", 5],
    ["abstract", 5],
    ["embers", 5],
    ["corruption", 5],
    ["sunburst", 5],
    ["stage lights", 5],
    ["fashion", 5],
    ["trick or treat", 5],
    ["fluffy", 5],
    ["symmetry", 5],
    ["reflective water", 5],
    ["glitch", 5],
    ["border", 5],
    ["framed", 5],
    ["character image", 5],
    ["3d", 5],
    ["lineart", 5],
    ["no lineart", 5],
    ["outline", 5],
    ["pixel art", 5],
    ["oekaki", 5],
    ["anime screencap", 5],
    ["game screenshot", 5],
    ["game cg", 5],
    ["fake screenshot", 5],
    ["drop shadow", 5],
    ["cut-in", 5],
    ["gradient", 5],
    ["film grain", 5],
    ["caustics", 5],
    ["bokeh", 5],
    ["bloom", 5],
    ["backlighting", 5],
    ["dithering", 5],
    ["halftone", 5],
    ["lens flare", 5],
    ["monochrome", 5],
    ["multiple monochrome", 5],
    ["silhouette", 5],
    ["vignetting", 5],
    ["chromatic aberration", 5],
    ["art deco", 5],
    ["art nouveau", 5],
    ["science fiction", 5],
    ["steampunk", 5],
    ["cyberpunk", 5],
    ["western", 5],
    ["sunlight", 5],
    ["wind", 5],
    ["squiggle", 5],
    ["limited palette", 5],
    ["overgrown", 5],
    ["cosmic horror", 5],
    ["halloween", 5],
    ["grass", 5],
    ["blood", 2],
]
eyeColors = [
    ["aqua eyes", 5],
    ["black eyes", 5],
    ["blue eyes", 5],
    ["brown eyes", 5],
    ["green eyes", 5],
    ["grey eyes", 5],
    ["orange eyes", 5],
    ["purple eyes", 5],
    ["pink eyes", 5],
    ["red eyes", 5],
    ["white eyes", 5],
    ["yellow eyes", 5],
    ["amber eyes", 5],
]
hairColors = [
    ["aqua hair", 5],
    ["black hair", 5],
    ["blonde hair", 5],
    ["blue hair", 5],
    ["light blue hair", 5],
    ["dark blue hair", 5],
    ["brown hair", 5],
    ["light brown hair", 5],
    ["green hair", 5],
    ["dark green hair", 5],
    ["light green hair", 5],
    ["grey hair", 5],
    ["orange hair", 5],
    ["pink hair", 5],
    ["purple hair", 5],
    ["light purple hair", 5],
    ["red hair", 5],
    ["white hair", 5],
]
hairMutiColors = [
    ["multicolored hair", 5],
    ["colored inner hair", 5],
    ["gradient hair", 5],
    ["rainbow hair", 5],
    ["split-color hair", 2],
    ["streaked hair", 5],
    ["two-tone hair", 5],
]
colorPalette = [
    ["aqua", 5],
    ["black", 5],
    ["blue", 5],
    ["brown", 5],
    ["grey", 5],
    ["orange", 5],
    ["pink", 5],
    ["purple", 5],
    ["red", 5],
    ["white", 5],
    ["yellow", 5],
    ["beige", 5],
    ["two-toned", 5],
    ["multicolored", 5],
    ["silver", 2],
    ["gold", 2],
    ["rainbow", 1],
]

nsfwData = "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"

tailWingFeatures = ["mermaid", "centaur", "lamia"]

holidayThemes = [
    ["christmas", 6],
    ["christmas tree", 6],
    ["santa hat", 6],
    ["santa costume", 6],
    ["merry christmas", 6],
    ["gift", 6],
    ["christmas ornaments", 6],
    ["gift box", 6],
    ["christmas lights", 6],
    ["holly", 6],
    ["reindeer antlers", 6],
    ["candy cane", 6],
    ["gingerbread", 6],
    ["fireplace", 6],
    ["chimney", 6],
    ["pine tree", 6],
    ["snowman", 6],
    ["snow", 6],
    ["winter", 6],
    ["winter clothes", 6],
    ["snowflake", 6],
    ["snowing", 6],
    ["snow", 6],
    ["mittens", 6],
    ["snowscape", 6],
    ["earmuffs", 6],
    ["star (symbol)", 6],
    ["snowflake background", 6],
    ["mistletoe", 6],
    ["wreath", 6],
    ["christmas wreath", 6],
]


class NsfwDecode(BaseModel):
    p: List[List[Union[str, int, List]]]
    mp: List[List[Union[str, int, List]]]
    n: List[List[Union[str, int, List]]]
    u: List[List[Union[str, int, List]]]
    nk: List[List[Union[str, int, List]]]
    bd: List[List[Union[str, int, List]]]
    nEx: List[List[Union[str, int, List]]]
    nSM: List[List[Union[str, int, List]]]
    nSA: List[List[Union[str, int, List]]]
    nSP: List[List[Union[str, int, List]]]
    nPM: List[List[Union[str, int, List]]]
    nPA: List[List[Union[str, int, List]]]
    nPP: List[List[Union[str, int, List]]]
    sMod: List[List[Union[str, int, List]]]
    sActMod: List[List[Union[str, int, List]]]
    sT: List[List[Union[str, int, List]]]
    h: str
    yu: str
    ya: str
    fu: str
    fwm: str
    fwf: str
    nw: str


def decode_nsfw_data(nsfw_data):
    # Decode the Base64 data to raw bytes
    decoded_data = base64.b64decode(nsfw_data)

    # Apply XOR operation on each byte with its index, and clamp values within the valid range
    decoded_array = bytearray(
        (decoded_data[i] ^ i) & 0xFF for i in range(len(decoded_data))
    )

    # Decode the resulting byte array into a UTF-8 string, and parse it as JSON
    return NsfwDecode.model_validate_json(decoded_array.decode('utf-8'))


def random_range(a, b):
    if a == b:
        return a
    if a > b:
        a, b = b, a
    return random.randint(a, b)


nsfwDecode = decode_nsfw_data(nsfwData)


def get_weighted_choice(options: Options,
                        tags: Optional[List[str]] = None) -> Any:
    filtered_options = []

    # 要么不存在第三个参数，要么第三个参数存在tags中的任意一个元素
    for option in options:
        if len(option) > 2:
            requirement = option[2]
            if isinstance(requirement, list) and any(tag in tags for tag in requirement):
                filtered_options.append(option)
        if len(option) <= 2:
            filtered_options.append(option)

    total_weight = sum(option[1] for option in filtered_options)
    random_weight = random_range(total_weight, 1)
    cumulative_weight = 0

    for option in filtered_options:
        cumulative_weight += option[1]
        if random_weight <= cumulative_weight:
            return option[0]

    raise ValueError("getWeightedChoice: should not reach here")


def generate_character_attributes(
        gender: str,
        view_type: Optional[str],
        is_nsfw: bool,
        level: int
) -> List[Any]:
    attributes: List[Any] = []

    # Adding attributes based on randomness
    if random.random() < 0.1:
        attributes.append(get_weighted_choice(animalFeatures, attributes))

    has_tail_or_wing_features = any(attr in tailWingFeatures for attr in attributes)

    if random.random() < 0.4:
        attributes.append(get_weighted_choice(skinColors, attributes))
    if random.random() < 0.8:
        attributes.append(get_weighted_choice(eyeColors, attributes))
    if random.random() < 0.1:
        attributes.append(get_weighted_choice(eyeStyles, attributes))
    if random.random() < 0.2:
        attributes.append(get_weighted_choice(strangeEyeEffects, attributes))
    if random.random() < 0.8:
        attributes.append(get_weighted_choice(hairLengths, attributes))
    if random.random() < 0.5:
        attributes.append(get_weighted_choice(braidStyles, attributes))
    if random.random() < 0.7:
        attributes.append(get_weighted_choice(hairColors, attributes))
    if random.random() < 0.1:
        attributes.extend(
            [get_weighted_choice(hairMutiColors, attributes), get_weighted_choice(hairColors, attributes)])
    if random.random() < 0.1:
        attributes.append(get_weighted_choice(hairStyles, attributes))
    if random.random() < 0.2:
        attributes.append(get_weighted_choice(bangsStyles, attributes))
    if gender.startswith("f") and random.random() < 0.5:
        attributes.append(get_weighted_choice(breastSizes, attributes))

    # Determine number of body features
    number_of_body_features: int
    if level == 1:
        number_of_body_features = get_weighted_choice(
            [
                [0, 10],
                [1, 30],
                [2, 15],
                [3, 5],
            ],
            attributes
        )
    elif level == 2:
        number_of_body_features = get_weighted_choice(
            [
                [0, 20],
                [1, 40],
                [2, 10],
            ],
            attributes
        )
    else:
        number_of_body_features = get_weighted_choice(
            [
                [0, 30],
                [1, 30],
            ],
            attributes
        )

    for _ in range(number_of_body_features):
        attributes.append(get_weighted_choice(bodyFeatures, attributes))

    if random.random() < 0.2:
        attributes.append(get_weighted_choice(hatTypes, attributes))
        if random.random() < 0.2:
            attributes.append(get_weighted_choice(hatAccessories, attributes))
    elif random.random() < 0.3:
        attributes.append(get_weighted_choice(hairAccessories, attributes))

    # Adding clothing options
    clothing_option = get_weighted_choice(
        [
            ["uniform", 10],
            ["swimsuit", 5],
            ["bodysuit", 5],
            ["normal clothes", 40],
        ],
        attributes
    )

    # Handling NSFW-specific clothing
    if is_nsfw and random.random() < 0.9:
        nsfw_choice = get_weighted_choice(
            [
                ["n", 15],
                ["u", 10],
                ["nk", 5],
            ],
            attributes
        )

        if nsfw_choice == "n":
            attributes.append(get_weighted_choice(nsfwDecode.n, attributes))
        elif nsfw_choice == "u":
            attributes.append(get_weighted_choice(nsfwDecode.u, attributes))
            if random.random() < 0.5:
                clothing_option = None  # Remove clothing
        elif nsfw_choice == "nk":
            attributes.append(get_weighted_choice(nsfwDecode.nk, attributes))
            clothing_option = None  # Remove clothing

        if view_type not in ("portrait", "upper body"):
            if gender == "f" and random.random() < 0.8:
                attributes.append(get_weighted_choice(nsfwDecode.p, attributes))
            elif gender == "m" and random.random() < 0.8:
                attributes.append(get_weighted_choice(nsfwDecode.mp, attributes))
            elif gender == "fu":
                attributes.append(get_weighted_choice(nsfwDecode.mp, attributes))
                if random.random() < 0.5:
                    attributes.append(get_weighted_choice(nsfwDecode.p, attributes))

    # Handling clothing-specific options
    if clothing_option == "uniform":
        attributes.append(get_weighted_choice(clothingArmor, attributes))
    elif clothing_option == "swimsuit":
        attributes.append(get_weighted_choice(swimwear, attributes))
    elif clothing_option == "bodysuit":
        attributes.append(get_weighted_choice(bodySuits, attributes))
    elif clothing_option == "normal clothes":
        if gender.startswith("f") and random.random() < 0.5:
            attributes.append(get_weighted_choice(legWearTypes, attributes))
            if random.random() < 0.2:
                attributes.append(get_weighted_choice(detailedLegWear, attributes))
        if gender.startswith("f") and random.random() < 0.2:
            add_color = random.random() < 0.5
            color = get_weighted_choice(colorPalette, attributes)
            dress = get_weighted_choice(dressStyles, attributes)
            attributes.append(f"{color} {dress}" if add_color else dress)
        else:
            if random.random() < 0.85:
                add_color = random.random() < 0.5
                color = get_weighted_choice(colorPalette, attributes)
                top = get_weighted_choice(topWear, attributes)
                attributes.append(f"{color} {top}" if add_color else top)
            if not has_tail_or_wing_features:
                if random.random() < 0.85 and view_type != "portrait":
                    add_color = random.random() < 0.5
                    color = get_weighted_choice(colorPalette, attributes)
                    bottom = get_weighted_choice(bottomWear, attributes)
                    attributes.append(f"{color} {bottom}" if add_color else bottom)
                if random.random() < 0.6 and (view_type == "full body" or view_type is None):
                    add_color = random.random() < 0.5
                    color = get_weighted_choice(colorPalette, attributes)
                    boots = get_weighted_choice(bootTypes, attributes)
                    attributes.append(f"{color} {boots}" if add_color else boots)

    if random.random() < 0.6:
        attributes.append(get_weighted_choice(facialExpressions, attributes))

    # Adding poses and actions
    if random.random() < (1 if is_nsfw and level == 1 else 0.4):
        poses_and_actions = posesAndActions + (nsfwDecode.nSM + nsfwDecode.nSA + nsfwDecode.nSP if is_nsfw else [])
        attributes.append(get_weighted_choice(poses_and_actions, attributes))

    # Filter for certain specific attributes
    if any(attr for attr in attributes if "sleeping" in attr or "zzz" in attr or "closed eyes" in attr):
        attributes = [attr for attr in attributes if attr not in [color[0] for color in eyeColors]]

    # Determine number of accessories
    accessory_count: int
    if level == 1:
        accessory_count = get_weighted_choice(
            [
                [0, 10],
                [1, 30],
                [2, 15],
                [3, 5],
            ],
            attributes
        )
    elif level == 2:
        accessory_count = get_weighted_choice(
            [
                [0, 20],
                [1, 40],
                [2, 10],
            ],
            attributes
        )
    else:
        accessory_count = get_weighted_choice(
            [
                [0, 30],
                [1, 30],
            ],
            attributes
        )

    for _ in range(accessory_count):
        accessories_combined = accessories + (nsfwDecode.nEx if is_nsfw else [])
        attributes.append(get_weighted_choice(accessories_combined, attributes))

    # Remove legwear attributes if tail or wing features present
    if has_tail_or_wing_features:
        attributes = [attr for attr in attributes if "legwear" not in attr]

    return attributes


def generate_tags(isNSFW: bool) -> str:
    """
    Generate tags for a character or scene based on whether it's NSFW or not.

    Args:
        isNSFW (bool): Indicates whether the content is NSFW.

    Returns:
        str: Comma-separated tags.
    """
    tags: List[str] = []
    is_explicit = isNSFW
    character_count = get_weighted_choice(
        [
            [1, 70],
            [2, 20],
            [3, 7],
            [0, 5],
        ],
        tags
    )
    if is_explicit:
        character_count = get_weighted_choice(
            [
                [1, 35],
                [2, 20],
                [3, 7],
            ],
            tags
        )
    if character_count == 0:
        tags.append("no humans")
        if random.random() < 0.3:
            tags.append(get_weighted_choice(artStyles, tags))

        tags.append(get_weighted_choice(sceneTypes, tags))

        environment_count = get_weighted_choice(
            [
                [2, 15],
                [3, 50],
                [4, 15],
                [5, 5],
            ],
            tags
        )
        for _ in range(environment_count):
            tags.append(get_weighted_choice(environmentElements, tags))

        small_object_count = get_weighted_choice(
            [
                [0, 15],
                [1, 10],
                [2, 20],
                [3, 20],
                [4, 20],
                [5, 15],
            ],
            tags
        )
        small_object_count -= character_count
        if small_object_count < 0:
            small_object_count = 0
        for _ in range(small_object_count):
            tags.append(get_weighted_choice(smallObjects, tags))

        return ", ".join(tags)

    background_option = None
    if random.random() < 0.3:
        tags.append(get_weighted_choice(artStyles, tags))

    male_count = female_count = other_count = 0

    for _ in range(character_count):
        gender = get_weighted_choice(
            [
                ["m", 30],
                ["f", 50],
                ["o", 10],
            ],
            tags
        )
        if gender == "m":
            male_count += 1
        elif gender == "f":
            female_count += 1
        else:
            other_count += 1

    if male_count == 1:
        tags.insert(0, "1boy")
    elif male_count == 2:
        tags.insert(0, "2boys")
    elif male_count == 3:
        tags.insert(0, "3boys")

    if female_count == 1:
        tags.insert(0, "1girl")
    elif female_count == 2:
        tags.insert(0, "2girls")
    elif female_count == 3:
        tags.insert(0, "3girls")

    if other_count == 1:
        tags.insert(0, "1other")
    elif other_count == 2:
        tags.insert(0, "2others")
    elif other_count == 3:
        tags.insert(0, "3others")

    has_NSFw_content = False
    # Handle explicit content
    if is_explicit:
        has_futa = False
        if male_count >= 2 and female_count == 0:
            if random.random() < 0.7:
                tags.append(nsfwDecode.yu)
            else:
                tags.append(nsfwDecode.fu)
                has_futa = True

        if female_count >= 2 and male_count == 0:
            tags.append(nsfwDecode.ya)

        mixed_content = male_count > 0 and female_count > 0 and random.random() < 0.2
        if mixed_content:
            tags.append(nsfwDecode.fu)

        if character_count >= 2:
            has_NSFw_content = True
            potential_NSFw_tags = nsfwDecode.nPM[:]

            if (male_count > 0 and female_count > 0) or has_futa:
                potential_NSFw_tags += nsfwDecode.nPP

            if female_count > 0 or has_futa:
                potential_NSFw_tags += nsfwDecode.nPA

            if has_futa:
                tags.append(nsfwDecode.fwf)

            if mixed_content:
                tags.append(nsfwDecode.fwm)

            tags.append(get_weighted_choice(potential_NSFw_tags, tags))

            if random.random() < 0.6:
                tags.append(get_weighted_choice(nsfwDecode.sMod, tags))

        if random.random() < 0.4:
            tags.append(get_weighted_choice(nsfwDecode.sActMod, tags))
        if random.random() < 0.05:
            tags.append(get_weighted_choice(nsfwDecode.bd, tags))
        if random.random() < 0.05:
            tags.append(get_weighted_choice(nsfwDecode.sT, tags))

        tags.insert(0, nsfwDecode.nw)

    # Background and setting
    if random.random() < 0.8:
        background_style = get_weighted_choice(backgroundStyles, tags)
        tags.append(background_style)

        if background_style == "scenery" and random.random() < 0.5:
            scenery_elements = random_range(3, 1)
            for _ in range(scenery_elements):
                tags.append(get_weighted_choice(environmentElements, tags))

    if random.random() < 0.3:
        tags.append(get_weighted_choice(cameraAngles, tags))

    if random.random() < 0.7 and not has_NSFw_content:
        background_option = get_weighted_choice(framingStyles, tags)
        tags.append(background_option)

    # Generate character-specific attributes
    for _ in range(male_count):
        include_futa_tag = is_explicit and male_count == 1 and character_count == 1 and random.random() < 0.2
        if include_futa_tag:
            tags.append(nsfwDecode.fu)
        tags.extend(generate_character_attributes("fu" if include_futa_tag else "m", background_option, is_explicit,
                                                  character_count))

    for _ in range(female_count):
        tags.extend(generate_character_attributes("f", background_option, is_explicit, character_count))

    for _ in range(other_count):
        tags.extend(generate_character_attributes("o", background_option, is_explicit, character_count))

    if random.random() < 0.2:
        object_count = random_range(4, 0)
        if character_count == 2:
            object_count = random_range(3, 0)
        for _ in range(object_count):
            tags.append(get_weighted_choice(smallObjects, tags))

    if random.random() < 0.25:
        effect_count = random_range(3, 1)
        for _ in range(effect_count):
            tags.append(get_weighted_choice(visualEffects, tags))

    if random.random() < 0.2:
        tags.append(get_weighted_choice(years, tags))
    if random.random() < 0.1:
        tags.append(get_weighted_choice(objectFocus, tags))

    # Remove duplicates, add optional special formatting
    tags = list({tag: True for tag in tags}.keys())
    for i in range(len(tags)):
        if random.random() < 0.02:
            tags[i] = f"{{{tags[i]}}}"

    return ", ".join(tags)


def is_holiday_season() -> bool:
    """
    Check if the current date is within the holiday season (December 1 - December 31).

    Returns:
        bool: True if it's holiday season, False otherwise.
    """
    today = datetime.now()
    return today.month == 12 and 1 <= today.day <= 31


def get_holiday_themed_tags() -> str:
    """
    Generate holiday-themed tags based on the current date.

    Returns:
        str: Comma-separated tags.
    """
    return get_weighted_choice(holidayThemes)


if __name__ == "__main__":
    is_nsfw = random.random() < 0.1
    print(generate_tags(is_nsfw))
    if is_holiday_season():
        print(get_weighted_choice(holidayThemes))
