"""Manually interpreted retrospective bakery pilot; no model/API calls."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from authoring import Annotation

a = Annotation("01_bakery", prompt_version="v0")

# One explicitly selected contextual POS per word, paragraph by paragraph.
TAGS = [
"n v v num n n adp det adj n conj adp n n pron v pron adp n n",
"v v det adj n n pron v n n adp n n",
"n n v adp det n n adp det n det pron adp det n adp n n",
"pron v det n adj n v n conj pron v v pron pron v pron det n v adv pron v pron v v adp n",
"pron v det n adp det n pron v det adj adj n",
"n n v pron adv v num adv pron v det adj n conj num n",
"det n v adj adp n n conj det adj n n n v adj n n n adp det n det n v adj conj det adj n v adp det n n adp pron",
"v pron v det n n n v pron v part v pron adv",
"n n v det adj n n conj v det adj n n adv v pron adj det n adp n n v adj conj det n v det n adp v conj pron v",
"pron v v",
"v pron adv adv pron v pron adp det n n",
"n v det n adp det n conj v det n pron v adv adp det n adp det n conj adp det n adp det adj n pron v det adj n adp pron v adj adp adj n n pron v v det adj adj n v adp det n",
"det adj n v v det det n adv n v adp det n det adj n v adp det n n",
"pron v adp det adj n",
"adv adv det n v adj adp det adj n adp det n det n v adv conj det n v det n det n v adp n n pron v v pron adj conj det n v v adv",
"conj pron v det n num n adp det n v v adp det n det n n v adj conj det adj n v v det adj n",
"n v det n adv adv adp n det n v adv adj",
"adp adv pron v n n n det n v adj conj det adj n adp n v adp pron n v",
"pron",
"pron v adv adv n n v n",
"det n v adv adv pron v adj",
"n v adp det n n n v pron adv pron v v det n adp det n v adv conj v det n adp n conj det n v v adv conj det n v adv v part v adj adp adv",
"pron v det adj n",
"pron v v det n v det n adp adv",
"pron v n v adv pron v pron part v pron",
"det n v det n n n v adv det adj n v adv adp det n pron v pron pron v det n",
"pron v conj pron v det n pron v pron v det n det n v adv",
"n n v adp pron adp det adj n adv pron v det n adv pron v det n pron v det n v adp adj n",
"pron v adj n v n",
"pron v adv adj n",
"pron v det n adv n n v det n adp det adj n n v det n adp n conj det adj n n v det n n adv adp det n det n v v det adv conj pron v part v adv",
"n n v det n det n v part v v",
"pron v v adp det n",
"conj det adj n v v v pron v part det adj n conj det adj pron adv v det adj n",
"n v det n adp det n n n v det n adp det n det n v conj pron v det n",
"pron v v det n n v",
"v adv adj adp n",
"v adv det adj n adp pron v det n",
"n n v det n conj v det n v adv adp det adj n conj pron v part det n n pron v det n conj det n v adp det adj n adp det adj n",
"pron v det n det n v adv adj pron adj pron adj conj pron adp det adj n n adp n",
"v det n pron v",
"pron v adp det n n v pron v det n",
"adv pron v pron v adp det adj n conj det n v adv adp det n det n n v adp n n adj adv adp det n n adj adv adv",
"conj pron v n n v pron adp det n v v det n adv adp det n adv pron v",
"n n v pron v",
"adv v pron v pron",
"adp pron det n n v adj conj adj adp det n det adj adj n v adp num n det n v adp pron adp det adj adj n",
]

# Deliberately listed lexical decisions; no stemming or suffix guessing.
LEMMAS = {
"Tessa": "Tessa", "Tessa’s": "Tessa", "Pike": "Pike", "Pike’s": "Pike", "Bakery": "Bakery",
"Mrs": "Mrs", "Mr": "Mr", "Hobb": "Hobb", "Hobb’s": "Hobb", "Mill": "Mill", "Lane": "Lane",
"Thursday": "Thursday", "HAPPY": "happy", "BIRTHDAY": "birthday", "MR": "Mr", "HOBB": "Hobb", "B": "B",
"had": "have", "has": "have", "was": "be", "were": "be", "are": "be", "I’d": "I", "I":"I",
"won’t": "will", "don’t": "do", "I’m": "I", "You’re": "you", "It’s": "it", "it’s": "it",
"I’ll": "I", "we’ll": "we", "could": "can", "would": "will", "should": "shall",
"saved": "save", "coins": "coin", "carried": "carry", "told": "tell", "paused": "pause",
"mended": "mend", "said": "say", "fixing": "fix", "remembered": "remember", "years": "year",
"made": "make", "counted": "count", "slid": "slide", "buys": "buy", "wrote": "write",
"letters": "letter", "leaned": "lean", "asked": "ask", "found": "find", "laid": "lay",
"folded": "fold", "stones": "stone", "tipping": "tip", "loaves": "loaf", "tucked": "tuck",
"held": "hold", "handles": "handle", "walked": "walk", "stopped": "stop", "night’s": "night",
"paved": "pave", "winding": "wind", "glanced": "glance", "shone": "shine", "turned": "turn",
"steepest": "steep", "rattled": "rattle", "wheels": "wheel", "jolted": "jolt", "bumped": "bump",
"froze": "freeze", "holding": "hold", "clattered": "clatter", "lifted": "lift", "shifted": "shift",
"smudged": "smudge", "pressed": "press", "reached": "reach", "curtains": "curtain", "showed": "show",
"knocked": "knock", "louder": "loud", "creaked": "creak", "looked": "look", "needed": "need",
"starting": "start", "called": "call", "opened": "open", "peered": "peer", "sticking": "stick",
"did": "do", "fixed": "fix", "swallows": "swallow", "came": "come", "wider": "wide",
"socks": "sock", "cleared": "clear", "moving": "move", "newspapers": "newspaper",
"tilted": "tilt", "fallen": "fall", "studied": "study", "seems": "seem", "swimming": "swim",
"got": "get", "gone": "go", "wandering": "wander", "smiled": "smile", "trembled": "tremble",
"lit": "light", "wishes": "wish", "lowered": "lower", "blew": "blow", "went": "go",
"switched": "switch", "slices": "slice", "paid": "pay", "replied": "reply", "ate": "eat",
"ticked": "tick", "sat": "sit", "left": "leave", "glowed": "glow", "iced": "ice",
"stood": "stand", "plates": "plate",
}
for paragraph, tags in enumerate(TAGS):
    a.tag(paragraph, tags, LEMMAS)
# Updated shared pilot convention: contractions keep the leading component's POS.
a.feature([20,397,635,669,674,681,803,820],pos="pron")

# Stable identities. A proper-name title and name share the denotation; parts,
# physical inscriptions and groups have separate identities from their carriers.
ENTITIES = [
("e1", "Tessa", "person", [0,14,20,26,53,58,66,78,80,144,149,151,190,192,206,217,234,247,267,280,313,315,327,355,370,388,391,397,398,407,417,450,465,467,470,495,505,521,549,555,579,639,667,749,754,782,794,799,817]),
("e2", "Mrs. Pike", "person", [28,29,33,34,37,91,92,118,119,157,158,199,412,413,814,815]),
("e3", "Mr. Hobb", "person", [31,32,44,51,60,64,67,71,123,124,372,373,395,396,455,462,472,481,482,485,498,500,503,507,517,518,527,532,560,561,600,601,624,646,647,658,662,669,674,682,684,685,687,700,706,722,747,756,761,796,797,803,812,825]),
("e4", "Tessa's nine coins", "coin_group", [5,16,81,85,94]),
("e5", "blue savings jar", "jar", [9]),
("e6", "Pike's Bakery", "bakery", [18,19,810]),
("e7", "birthday cake", "cake", [25,103,108,155,209,271,277,335,364,421,459,475,582,589,595,611,635,638,725,753,839,844,848]),
("e8", "Mrs. Pike's rolling pin", "rolling_pin", [39]),
("e9", "Mill Lane", "lane", [49,50,177,178,229]),
("e10", "Tessa's kite", "kite", [54,63,506,535,536]),
("e11", "Mr. Hobb's birthday", "birthday", [68,499,683]),
("e12", "bakery counter", "counter", [84]),
("e13", "two returned coins", "coin_subgroup", [97]),
("e14", "seven payment coins", "coin_subgroup", [99]),
("e15", "birthday candle", "candle", [106,642,692,845]),
("e16", "lemon icing", "icing", [113,274,604]),
("e17", "blue icing border", "icing_border", [117]),
("e18", "birthday inscription", "inscription", [129]),
("e19", "final B decoration", "letter_decoration", [135,142,349,354,620]),
("e20", "icing flower", "icing_flower", [140,343,606,741,746,759]),
("e21", "borrowed wicker delivery basket", "basket", [148,163,172,183,196,201,212,310,318,411,415,430,558,587,779,806,823]),
("e22", "folded tea towel", "tea_towel", [169,789]),
("e23", "Mill Lane stones", "stone_group", [175]),
("e24", "basket handles", "handle_pair", [216]),
("e25", "village green", "green", [222]),
("e26", "village well", "well", [225]),
("e27", "old bridge", "bridge", [233,240]),
("e28", "short muddy path", "path", [238]),
("e29", "last night's rain", "rain_episode", [246]),
("e30", "long paved way", "road", [253,260,285,287,308]),
("e31", "hill", "hill", [257,298,616]),
("e32", "cake paper cover", "paper_cover", [279,330]),
("e33", "paved-way stones", "stone_group", [289]),
("e34", "passing cart", "cart", [300,304,322]),
("e35", "cart wheels", "wheel_group", [305]),
("e36", "Tessa's knee", "body_part", [314]),
("e37", "cake box", "box", [340,358,583]),
("e38", "Mr. Hobb's cottage", "cottage", [374,402,464,559]),
("e39", "kitchen curtains", "curtain_pair", [376,387,709]),
("e40", "cottage lamplight", "light", [384]),
("e41", "cottage floorboard", "floorboard", [400]),
("e42", "cottage doorstep", "doorstep", [424]),
("e43", "Tessa's home", "home", [426]),
("e44", "evening drizzle", "rain_episode", [435,771]),
("e45", "cottage door", "door", [477,530]),
("e46", "Mr. Hobb's hair", "hair", [487]),
("e47", "returning swallows", "swallow_group", [514]),
("e48", "kite tail", "kite_tail", [539]),
("e49", "kite-tail socks", "sock_group", [543,544,547,550,554]),
("e50", "small kitchen table", "table", [569,768,835]),
("e51", "newspaper stack", "newspaper_group", [572,574]),
("e52", "single mug", "mug", [578]),
("e53", "Mr. Hobb's smile", "facial_expression", [629,633]),
("e54", "match", "match", [650,654]),
("e55", "drawer", "drawer", [653]),
("e56", "match flame", "flame", [655]),
("e57", "candle wick", "wick", [661]),
("e58", "Mr. Hobb's head", "body_part", [688]),
("e59", "kitchen light", "lamp", [705]),
("e60", "kitchen window", "window", [712,717,776,828]),
("e61", "cake slices", "slice_group", [727]),
("e62", "tall cake slice", "cake_slice", [731]),
("e63", "thin cake slice", "cake_slice", [733]),
("e64", "flower-topped cake slice", "cake_slice", [736]),
("e65", "Tessa and Mr. Hobb", "person_group", [763,820,821]),
("e66", "Tessa's chair", "chair", [783]),
("e67", "cottage gate", "gate", [802]),
("e68", "two plates", "plate_pair", [843]),
]
for eid, name, kind, mentions in ENTITIES:
    a.entity(eid, name, kind, mentions)

# Each dialogue turn has its own scope; nested reports/conditions get children.
QUOTES = [
("s1",20,26,"e1"),("s2",30,33,"e1"),("s3",43,51,"e2"),
("s4",51,57,"e1"),("s5",59,78,"e1"),("s6",99,107,"e2"),
("s7",121,125,"e2"),("s8",143,149,"e1"),("s9",151,157,"e1"),
("s10",171,192,"e2"),("s11",192,195,"e1"),("s12",195,206,"e2"),
("s13",395,399,"e1"),("s14",455,460,"e3"),("s15",465,467,"e1"),
("s16",470,476,"e1"),("s17",493,500,"e3"),("s18",500,517,"e1"),
("s19",532,544,"e3"),("s20",544,548,"e1"),("s21",550,555,"e3"),
("s22",605,611,"e3"),("s23",611,617,"e1"),("s24",617,624,"e3"),
("s25",634,639,"e3"),("s26",662,667,"e1"),("s27",669,674,"e3"),
("s28",674,684,"e1"),("s29",744,747,"e3"),("s30",749,754,"e1"),
("s31",756,760,"e1"),("s32",803,812,"e3"),("s33",814,819,"e1"),
("s34",819,824,"e3"),
]
for sid, start, stop, holder in QUOTES:
    a.scope(sid,range(start,stop),kind="quotation",holder_id=holder,
            description="Direct speech; speaker assertions remain distinct from narrator evidence.")
a.scopes["s7"]["kind"] = "inscription"
a.scopes["s7"]["description"] = "Cake inscription written by Mrs. Pike, not an audible turn."
a.scope("s35",range(67,71),kind="reported_content",parent="s5",holder_id="e3",description="Tessa reports Hobb's birthday statement from last spring; today is Tessa's current deictic reformulation.")
a.scope("s36",range(73,78),kind="reported_content",parent="s5",holder_id="e3",description="Hobb's reported claim that nobody had remembered his birthday for years; not independently established narrator fact.")
a.scope("s37",range(188,192),kind="conditional",parent="s10",holder_id="e2",description="Habitual tipping conditional on rushing, not an actual tipping occurrence.")
a.scope("s38",range(258,267),kind="hypothetical",holder_id="e1",description="Prospective duration comparison of the longer route, not a measured trip duration.")
a.scope("s39",range(417,433),kind="considered_plan",holder_id="e1",description="Tessa considers leaving the cake, hurrying home and returning the basket; this branch is not executed.")
a.scope("s40",range(440,450),kind="hypothetical",holder_id="e1",description="Consequence of leaving cake outside in drizzle, not actual destruction.")
a.scope("s41",range(509,517),kind="reported_content",parent="s18",holder_id="e3",description="Tessa recalls Hobb's description of his birthday using returning swallows.")
a.scope("s42",range(536,544),kind="remembered",parent="s19",holder_id="e3",description="Hobb's remembered kite-tail description, corroborated in subsequent dialogue.")
a.scope("s43",range(607,611),kind="figurative",parent="s22",holder_id="e3",description="Playful description of smudged icing as swimming, not literal animate motion.")
a.scope("s44",range(621,624),kind="figurative",parent="s24",holder_id="e3",description="Damaged letter described as wandering, not independent travel.")
a.scope("s45",range(817,819),kind="reported_directive",parent="s33",holder_id="e2",description="Tessa reports Mrs. Pike's earlier instruction; no second actual Pike utterance is asserted here.")

# A concise event table is manually selected, rather than tagging all verbs as
# actions. Auxiliary/copular grammar is added separately below.
N = 0
EVENT_AT = {}
def ev(w,label,actor=None,patients=(),type="other",roles=None,scope=None,factuality=None,**fields):
    global N
    # These are later descriptions of the same underlying event/state, not
    # extra repairs, payments or birthday conversations.
    reuse = {62:52, 504:52, 508:65, 494:65, 501:65, 414:200, 750:100}
    if w in reuse:
        eid = EVENT_AT[reuse[w]][0]
        a.mention_event(eid,w,role="action",note="Retrospective coreference to the same underlying event/state.")
        for role, mentions in (roles or {}).items():
            a.mention_event(eid,mentions,role=role)
        EVENT_AT[w]=[eid]
        return eid
    N += 1
    eid=f"ev{N}"
    scope=scope or a.words[w]["scope_id"]
    if factuality is None:
        factuality="asserted" if scope=="s0" else "reported"
    a.event(eid,w,label,type=type,actor=actor,patients=patients,roles=roles or {},
            scope=scope,factuality=factuality,support=[w],**fields)
    EVENT_AT.setdefault(w,[]).append(eid)
    return eid

# Narrated events and their argument mentions. States use the property head;
# mental predicates use holders, and their content remains scoped separately.
ev(2,"save nine coins","e1",["e4"],"obtain",{"actor":[0],"patient":[5]})
ev(15,"carry coins to bakery","e1",["e4"],"move",{"actor":[14],"patient":[16],"destination":[18,19]})
ev(21,"request birthday cake","e1",["e7"],"state",{"actor":[20],"patient":[25],"beneficiary":[31,32]},factuality="desired")
ev(27,"tell baker cake request","e1",[],"speak",{"actor":[26],"recipient":[28,29]},recipient="e2")
ev(35,"pause with rolling pin","e2",[],"other",{"actor":[33,34],"instrument":[39]},instruments=["e8"])
ev(52,"repair Tessa's kite","e3",["e10"],"repair",{"actor":[51],"patient":[54]})
ev(57,"explain Hobb's earlier help","e1",[],"speak",{"actor":[58]},recipient="e2")
ev(62,"repair kite during conversation","e3",["e10"],"repair",{"actor":[60],"patient":[63]})
ev(65,"tell Tessa birthday date","e3",[],"speak",{"actor":[64],"recipient":[66]},recipient="e1")
ev(69,"birthday falls on reported day",None,["e11"],"state",{"subject":[68]})
ev(72,"report unremembered birthdays","e3",[],"speak",{"actor":[71]})
ev(75,"remember Hobb's birthday",None,["e11"],"state",{"quantified_actor":[73]},factuality="negated")
ev(79,"put coins on counter","e1",["e4"],"move",{"actor":[78],"patient":[81],"location":[84]})
ev(86,"coins form clinking pile",None,["e4"],"state",{"subject":[85],"result":[90]})
ev(93,"count Tessa's coins","e2",["e4"],"other",{"actor":[91,92],"patient":[94]})
ev(96,"return two coins","e2",["e13"],"transfer",{"patient":[97]},recipient="e1")
ev(100,"payment buys cake and candle","e1",["e7","e15"],"obtain",{"payment":[99],"patient":[103,106]})
ev(110,"cake is round",None,["e7"],"state",{"subject":[108]})
ev(120,"write birthday inscription","e2",["e18"],"other",{"actor":[118,119],"content":[121,122,123,124],"location":[127]})
ev(131,"inscription letters are neat",None,["e18"],"state",{"subject":[129]})
ev(136,"final B leans into icing flower",None,["e19"],"state",{"subject":[135],"landmark":[140]})
ev(145,"request temporary basket loan","e1",["e21"],"obtain",{"actor":[144],"patient":[148]},factuality="desired")
ev(150,"ask for delivery basket","e1",[],"speak",{"actor":[149]},recipient="e2")
ev(152,"want careful cake transport","e1",[],"state",{"actor":[151]})
ev(154,"carry cake carefully","e1",["e7"],"move",{"patient":[155]},factuality="desired")
ev(159,"find delivery basket","e2",["e21"],"obtain",{"actor":[157,158],"patient":[163]})
ev(165,"lay folded towel inside basket","e2",["e22"],"move",{"patient":[169],"location":[170]})
ev(171,"instruct Tessa to keep basket level","e1",["e21"],"state",{"patient":[172]},factuality="desired")
ev(180,"lane stones are uneven",None,["e23"],"state",{"subject":[175],"location":[177,178]})
ev(184,"basket has tipping tendency",None,["e21"],"state",{"subject":[183]})
ev(188,"basket tips when carrier rushes",None,["e21"],"move",factuality="hypothetical")
ev(191,"carrier rushes","e1",[],"move",{"actor":[190]},factuality="hypothetical")
ev(194,"commit not to rush","e1",[],"move",{"actor":[192]},factuality="negated")
ev(195,"return borrowed basket tomorrow","e1",["e21"],"transfer",{"patient":[196]},recipient="e2",factuality="desired")
ev(200,"need basket for morning loaves","e2",["e21"],"state",{"actor":[199],"patient":[201],"purpose":[205]})
ev(207,"put cake inside basket","e1",["e7"],"move",{"actor":[206],"patient":[209],"container":[212]})
ev(214,"hold both basket handles","e1",["e24"],"state",{"patient":[216]})
ev(218,"walk slowly along lane","e1",[],"move",{"actor":[217],"waypoint":[222,225],"route":[229]})
ev(235,"stop at old bridge","e1",[],"move",{"actor":[234],"location":[233]})
ev(242,"short path is muddy",None,["e28"],"state",{"subject":[238],"cause":[246]})
ev(249,"see longer paved route","e1",["e30"],"perceive",{"actor":[247],"patient":[253]})
ev(254,"route winds around hill",None,["e30"],"state",{"subject":[253],"landmark":[257]})
ev(262,"long route costs extra half hour",None,["e30"],"state",{"subject":[260],"duration":[263,265]},factuality="hypothetical")
ev(268,"glance at cake","e1",["e7"],"perceive",{"actor":[267],"patient":[271]})
ev(275,"blue icing shines through cover",None,["e16"],"state",{"subject":[274],"medium":[279]})
ev(281,"turn toward paved way","e1",[],"move",{"actor":[280],"route":[285]})
ev(291,"paved-route stones are lumpy",None,["e33"],"state",{"subject":[289]})
ev(301,"cart rattles past", "e34",[],"move",{"actor":[300],"location":[298]})
ev(306,"cart wheels jolt road","e35",["e30"],"other",{"actor":[305],"patient":[308]})
ev(311,"basket bumps Tessa's knee","e21",["e36"],"other",{"actor":[310],"patient":[314]})
ev(316,"Tessa stops moving suddenly","e1",[],"move",{"actor":[315]})
ev(317,"hold basket level","e1",["e21"],"state",{"patient":[318]})
ev(324,"cart clatters away","e34",[],"move",{"actor":[322]})
ev(328,"lift cake paper cover","e1",["e32"],"move",{"actor":[327],"patient":[330]})
ev(337,"cake corner shifts against box",None,["e7"],"move",{"patient":[335],"landmark":[340]})
ev(345,"icing flower is smudged",None,["e20"],"state",{"subject":[343]})
ev(351,"final B becomes blue squiggle",None,["e19"],"state",{"subject":[349],"result":[354]})
ev(356,"press cake box back into position","e1",["e37"],"move",{"actor":[355],"patient":[358]})
ev(367,"cake remains whole",None,["e7"],"state",{"subject":[364]})
ev(371,"reach Hobb's cottage","e1",[],"move",{"actor":[370],"destination":[374]})
ev(378,"cottage curtains are shut",None,["e39"],"state",{"subject":[376]})
ev(385,"lamplight shows beneath curtains",None,["e40"],"state",{"subject":[384],"landmark":[387]})
ev(389,"knock on Hobb's door first time","e1",["e45"],"other",{"actor":[388]})
ev(390,"no observable response to first knock",None,[],"state",factuality="negated")
ev(392,"knock on Hobb's door second time","e1",["e45"],"other",{"actor":[391]})
ev(397,"caller is Tessa",None,["e1"],"state",{"identity":[398]})
ev(401,"floorboard creaks",None,["e41"],"other",{"subject":[400],"location":[402]})
ev(406,"interior becomes quiet",None,["e38"],"state")
ev(408,"look at basket","e1",["e21"],"perceive",{"actor":[407],"patient":[411]})
ev(414,"Pike needs basket tomorrow","e2",["e21"],"state",{"actor":[412,413],"patient":[415]})
ev(419,"consider leaving cake on doorstep","e1",["e7"],"move",{"actor":[417],"patient":[421],"location":[424]},factuality="hypothetical")
ev(425,"consider hurrying home","e1",[],"move",{"destination":[426]},factuality="hypothetical")
ev(428,"consider returning basket before dark","e1",["e21"],"transfer",{"patient":[430]},recipient="e2",factuality="hypothetical")
ev(437,"drizzle starts again",None,["e44"],"other",{"subject":[435]})
ev(442,"cake left outside",None,["e7"],"state",factuality="hypothetical")
ev(446,"outside cake fails to remain whole",None,["e7"],"state",factuality="hypothetical")
ev(451,"knock on Hobb's door third time","e1",["e45"],"other",{"actor":[450]})
ev(457,"Hobb does not want cake","e3",["e7"],"state",{"actor":[455],"patient":[459]},factuality="negated")
ev(460,"call refusal from inside","e3",[],"speak",{"actor":[462],"source":[464]},recipient="e1")
ev(466,"acknowledge Hobb's stated preference","e1",[],"state",{"actor":[465]})
ev(468,"call back to Hobb","e1",[],"speak",{"actor":[467]},recipient="e3")
ev(471,"want Hobb to have cake","e1",[],"state",{"actor":[470]})
ev(474,"Hobb receives cake","e3",["e7"],"obtain",{"actor":[472],"patient":[475]},factuality="desired")
ev(478,"door opens slightly",None,["e45"],"state",{"subject":[477]})
ev(483,"Hobb peers outside","e3",[],"perceive",{"actor":[481,482]})
ev(488,"Hobb's hair sticks upward",None,["e46"],"state",{"subject":[487]})
ev(494,"ask who disclosed birthday","e3",[],"speak",{"recipient":[495]},recipient="e1")
ev(501,"Tessa identifies Hobb as prior teller","e1",[],"speak",{"reported_teller":[500]},recipient="e3")
ev(504,"recall Hobb fixing kite","e3",["e10"],"repair",{"actor":[503],"patient":[506]})
ev(508,"recall Hobb's swallow-date statement","e3",[],"speak",{"actor":[507]})
ev(510,"birthday matches swallow return day",None,["e11"],"state",{"day":[512]})
ev(515,"swallows return","e47",[],"move",{"actor":[514]})
ev(519,"Hobb looks at Tessa","e3",["e1"],"perceive",{"actor":[517,518],"patient":[521]})
ev(528,"Hobb opens door wider","e3",["e45"],"other",{"actor":[527],"patient":[530]})
ev(533,"remember Tessa's kite","e3",["e10"],"state",{"actor":[532],"patient":[535]})
ev(537,"kite had sock tail",None,["e10"],"state",{"subject":[536],"part":[539]})
ev(540,"tail made from old socks",None,["e48"],"state",{"material":[543]})
ev(546,"Tessa evaluates socks as good",None,["e49"],"state",{"subject":[544,547]})
ev(548,"Tessa defends sock quality","e1",[],"speak",{"actor":[549]},recipient="e3")
ev(553,"Hobb describes colorful socks",None,["e49"],"state",{"subject":[550,554]})
ev(556,"carry basket into cottage","e1",["e21"],"move",{"actor":[555],"patient":[558],"destination":[559]})
ev(562,"clear place at kitchen table","e3",["e50"],"other",{"actor":[560,561],"location":[569]})
ev(570,"move newspapers and mug","e3",["e51","e52"],"move",{"patient":[572,574,578]})
ev(580,"lift cake box from basket","e1",["e37"],"move",{"actor":[579],"patient":[583],"source":[587]})
ev(591,"cake has tilted",None,["e7"],"state",{"subject":[589]})
ev(598,"cake has not fallen apart",None,["e7"],"state",{"subject":[595]},factuality="negated")
ev(602,"study cake icing","e3",["e16"],"perceive",{"actor":[600,601],"patient":[604]})
ev(607,"flower appears to swim",None,["e20"],"state",{"subject":[606]})
ev(613,"report cake bumped on hill",None,["e7"],"other",{"patient":[611],"location":[616]})
ev(622,"letter playfully described as wandering",None,["e19"],"state",{"subject":[620]})
ev(625,"Hobb smiles genuinely","e3",[],"feel",{"actor":[624],"expression":[629,633]})
ev(637,"Hobb evaluates cake as fine",None,["e7"],"state",{"subject":[635,638]})
ev(640,"set candle in cake center","e1",["e15"],"move",{"actor":[639],"patient":[642],"location":[645]})
ev(648,"find match in drawer","e3",["e54"],"obtain",{"actor":[646,647],"patient":[650],"source":[653]})
ev(656,"match flame trembles",None,["e56"],"state",{"subject":[655]})
ev(659,"light candle wick","e3",["e57"],"other",{"actor":[658],"patient":[661]},instruments=["e54"])
ev(664,"suggest Hobb make a wish","e3",[],"state",{"actor":[662],"content":[666]},factuality="desired")
ev(668,"Tessa suggests birthday wish","e1",[],"speak",{"actor":[667]},recipient="e3")
ev(671,"Hobb claims too old for wishes","e3",[],"state",{"actor":[669]})
ev(677,"Tessa says Hobb is right age","e3",[],"state",{"actor":[674]})
ev(681,"Tessa affirms birthday",None,["e11"],"state",{"subject":[683]})
ev(686,"lower head","e3",["e58"],"move",{"actor":[684,685],"patient":[688]})
ev(690,"blow at candle","e3",["e15"],"other")
ev(693,"candle extinguishes",None,["e15"],"state",{"subject":[692]})
ev(701,"switch on kitchen light","e3",["e59"],"other",{"actor":[700],"patient":[705]})
ev(707,"open kitchen curtains","e3",["e39"],"other",{"actor":[706],"patient":[709]})
ev(713,"window becomes bright square",None,["e60"],"state",{"subject":[712],"result":[717]})
ev(723,"cut birthday cake","e3",["e7"],"other",{"actor":[722],"patient":[725]})
ev(728,"cake slices emerge uneven",None,["e61"],"state",{"subject":[727],"members":[731,733,736]})
ev(744,"offer flower-topped slice to Tessa","e1",["e64"],"obtain",{"patient":[746]},factuality="desired")
ev(748,"Hobb offers icing flower","e3",[],"speak",{"actor":[747]},recipient="e1")
ev(750,"Tessa states she paid for cake","e1",["e7"],"transfer",{"actor":[749],"patient":[753]})
ev(755,"Tessa replies flower is for Hobb","e1",[],"speak",{"actor":[754]},recipient="e3")
ev(757,"assign flower-topped slice to Hobb","e3",["e64"],"obtain",{"actor":[756],"patient":[759]},factuality="desired")
ev(762,"Hobb takes flower-topped slice","e3",["e64"],"obtain",{"actor":[761]})
ev(764,"Tessa and Hobb eat cake","e65",["e7"],"other",{"actor":[763],"location":[768]})
ev(772,"rain ticks against window",None,["e44"],"other",{"subject":[771],"landmark":[776]})
ev(780,"basket rests beside chair",None,["e21"],"state",{"subject":[779],"landmark":[783]})
ev(784,"basket is empty of cake",None,["e21"],"state",{"subject":[779]})
ev(790,"tea towel remains folded inside",None,["e22"],"state",{"subject":[789]})
ev(795,"Tessa leaves cottage","e1",[],"move",{"actor":[794]})
ev(798,"Hobb accompanies Tessa to gate","e3",["e1"],"move",{"actor":[796,797],"companion":[799],"destination":[802]})
ev(804,"Hobb promises basket return","e3",["e21"],"transfer",{"actor":[803],"patient":[806],"destination":[810]},factuality="desired",recipient="e2")
ev(813,"Hobb offers return task","e3",[],"speak",{"actor":[812]},recipient="e1")
ev(816,"Tessa reports Pike's return instruction","e2",[],"speak",{"reported_speaker":[814,815]})
ev(818,"Tessa obligated to return basket","e1",["e21"],"transfer",{"actor":[817]},factuality="desired",recipient="e2")
ev(822,"propose joint basket return","e65",["e21"],"transfer",{"actor":[820,821],"patient":[823]},factuality="desired",recipient="e2")
ev(829,"kitchen window glows warmly",None,["e60"],"state",{"subject":[828]})
ev(840,"cake remains between plates",None,["e7"],"state",{"subject":[839],"location":[835],"landmark":[843]})
ev(846,"candle lies beside cake",None,["e15"],"state",{"subject":[845],"landmark":[848]})

# Additional features, evidence and feedback follow below.

def E(w):
    return EVENT_AT[w][0]

def bundle(entity, value, w, status="asserted"):
    if status not in {"asserted","attributed_claim","candidate"}:
        status="attributed_claim"
    return dict(entity_id=entity,scope_id=a.words[w]["scope_id"],assertion_status=status,value=value)

def prop(pid,text,words,scope="s0",**metadata):
    a.proposition(pid,text,words,scope_id=scope,**metadata)

def feat(w, **fields):
    a.feature(w,**fields)

def world(w,key,entity,value,*,evidence=None,note=None,status="asserted"):
    a.feature(w,**{key:bundle(entity,value,w,status)},evidence=evidence,note=note)

# Prototype extension: no existing field covers a nonliteral visual simile or
# novel metaphor without misleadingly calling it irony or lexical idiom.
a.extension("figurative_mapping","object",
    "A text-supported metaphor or simile linking a target referent to a source image without asserting source-domain events or identity.",
    "current figurative expression",
    "irony_interpretation requires communicative irony; lexical_idiom_reading requires a conventional idiom; neither covers the novel cake-decoration metaphors or candle/twig simile.",
    {"target_id":"e20","source_image":"swimming","kind":"metaphor","literal_event":False})

# Quantities and interpretation propositions.
PROPS = [
("p1","Tessa obtains a birthday cake for Mr. Hobb.",[20,21,25,31,32],"s1"),
("p2","Hobb repaired Tessa's kite last spring.",[51,52,54,55,56,504,506],"s4"),
("p3","Thursday, the story's current day, is Hobb's birthday.",[12,65,68,69,70,499,508,512,514,515,683],"s35"),
("p4","Nobody had remembered Hobb's birthday for years.",[71,72,73,74,75,77],"s36"),
("p5","Tessa transports the cake carefully.",[151,152,154,155,156],"s9"),
("p6","The basket may tip if its carrier rushes.",[183,184,186,188,189,190,191],"s37"),
("p7","Tessa does not rush during the delivery.",[192,193,194],"s11"),
("p8","Tessa returns the borrowed basket to Pike tomorrow.",[195,196,198,199,200,201,204,205,814,815,816,817,818],"s12"),
("p9","Mrs. Pike needs the basket for tomorrow's morning loaves.",[199,200,201,204,205,412,413,414,415,416],"s12"),
("p10","The short route is muddy after last night's rain.",[238,242,244,245,246],"s0"),
("p11","The long route would add half an hour.",[260,261,262,263,264,265,266],"s38"),
("p12","Tessa chooses the longer paved route.",[268,271,280,281,285],"s0"),
("p13","The cake's flower and last B are visibly smudged after the basket bump.",[311,337,343,345,349,351,354],"s0"),
("p14","The cake remains structurally whole despite damaged decorations.",[364,367,589,591,595,597,598],"s0"),
("p15","Tessa leaves cake outside, goes home and returns the basket before dark.",list(range(417,433)),"s39"),
("p16","Cake left outside in the drizzle would not stay whole for long.",[435,437,441,442,443,444,445,446,447,449],"s40"),
("p17","Hobb does not want a cake.",[455,456,457,459],"s14"),
("p18","Hobb has a birthday cake.",[470,471,472,474,475],"s16"),
("p19","Tessa's kite had a tail made from old socks.",[532,533,535,536,537,539,540,543],"s19"),
("p20","Tessa calls the socks good; Hobb calls them colorful.",[544,546,547,550,553,554],"s20"),
("p21","The damaged cake is nevertheless fine.",[634,635,637,638],"s25"),
("p22","Hobb makes a birthday wish.",[662,663,664,666],"s26"),
("p23","Hobb is too old for wishes.",[669,670,671,673],"s27"),
("p24","Hobb is exactly the right age for a wish on his birthday.",[674,675,677,678,680,681,683],"s28"),
("p25","Tessa and Hobb share cake at the kitchen table.",[763,764,768],"s0"),
("p26","Hobb returns the basket tomorrow.",[803,804,806,810,811],"s32"),
("p27","Hobb and Tessa return the basket together tomorrow.",[819,820,821,822,823],"s34"),
("p28","The initially curtained window ends bright and the cake is shared between two plates.",[376,378,709,712,713,717,828,829,835,839,843],"s0"),
]
for args in PROPS:
    prop(*args)

# Function words receive appropriate grammatical/operator features, based on
# their already manually selected POS. These do not infer POS or semantic roles.
for r in a.words:
    w,t,pos=r["word_index"],r["token"].casefold(),r["pos"]
    if pos=="det" and t in {"a","an","the"}:
        feat(w,determiner_kind="definite_article" if t=="the" else "indefinite_article",
             definiteness="definite" if t=="the" else "indefinite")
    if pos=="det" and t in {"my","her","his","its","your"}:
        feat(w,determiner_kind="possessive",possessive_construction="possessive_determiner",definiteness="definite")
    if pos=="conj" and t=="and":
        feat(w,coordinator_type="conjunctive")
    if pos=="conj" and t=="but":
        feat(w,coordinator_type="adversative",discourse_relation_kind="contrast")
    if pos=="conj" and t in {"when","while","until"}:
        feat(w,subordinator_type="temporal",temporal_signal_relation={"when":"at_or_during","while":"overlap","until":"upper_boundary"}[t])
    if pos=="conj" and t=="though":
        feat(w,subordinator_type="concession",discourse_relation_kind="concession")
    if pos=="adp":
        feat(w,dependency_relation="prepositional_marker")
    if pos=="part" and t=="to":
        feat(w,dependency_relation="infinitival_marker",clause_finiteness="nonfinite")
    if pos=="pron" and t in {"i","she","he","we","you","they","them","her","him","me"}:
        person=1 if t in {"i","we"} else 2 if t=="you" else 3
        feat(w,mention_form="personal_pronoun",grammatical_person=person,
             grammatical_case="objective" if t in {"them","her","him","me"} else "nominative")
    if pos=="n" and r.get("entity_id"):
        feat(w,referent_kind="group" if a.entities[r["entity_id"]]["type"].endswith(("group","pair")) else "individual")

for w in [0,18,19,28,29,31,32,33,34,49,50,58,91,92,118,119,123,124,149,157,158,177,178,206,267,313,355,372,373,388,395,396,398,407,412,413,467,481,482,517,518,549,560,561,579,600,601,639,646,647,667,684,685,754,782,796,797,814,815]:
    feat(w,mention_form="proper_name",grammatical_number="singular")
for w in [28,31,33,91,118,123,157,372,395,412,481,517,560,600,646,684,796,814]:
    feat(w,proper_name_structure="title_plus_name")
for w in [18,245,313,373,782]:
    feat(w,genitive_realization="singular_s_clitic",possessive_construction="prenominal_s_genitive")
for w in [5,77,129,175,205,216,289,305,376,514,543,547,554,574,673,692-0+17,727,843]:
    feat(w,grammatical_number="plural")
for w in [16,85,544,550,763]:
    feat(w,grammatical_number="plural")
feat(215,predeterminer_kind="universal",cardinal_value=2)
feat(821,quantity_distribution_cue="joint_pair",split_antecedent_ids=["e1","e3"])
feat([763,820],split_antecedent_ids=["e1","e3"],group_members=["e1","e3"],grammatical_number="plural")

for w, expansion in {20:["I","would"],193:["will","not"],397:["it","is"],456:["do","not"],635:["it","is"],669:["I","am"],674:["you","are"],681:["it","is"],803:["I","will"],820:["we","will"]}.items():
    feat(w,contraction_expansion=expansion,verb_form="finite")
feat([193,456],polarity="negative",negation_marker_form="not")
feat([445,597,626],negation_marker_form="not",polarity="negative")
feat(456,do_support_status="negative_support")
feat(143,modal_auxiliary_class="possibility_family",subject_auxiliary_inversion=True,modal_base={"kind":"permission","holder":"e1"})
feat(193,modal_auxiliary_class="volitional_future",modal_base={"kind":"commitment","holder":"e1"})
feat(248,modal_auxiliary_class="possibility_family",modal_base={"kind":"perceptual_ability","holder":"e1"})
feat(261,modal_base={"kind":"prospective_route_comparison","holder":"e1"})
feat(418,modal_base={"kind":"available_plan","holder":"e1"})
feat(444,modal_base={"kind":"conditional_prediction","holder":"e1"})
feat([663,818],modal_auxiliary_class="necessity_family",modal_base={"kind":"recommendation_or_obligation"})
feat([501,762],verb_phrase_ellipsis=True,verb_phrase_anaphor="do",verb_form="finite",tense="past")
feat(501,event_antecedent_id=E(65))
feat(762,event_antecedent_id=E(757))
feat(818,verb_phrase_ellipsis=True,coordination_ellipsis_source_id=a.anchor(195))

# Explicit finite/nonfinite decisions; auxiliaries keep their own morphology.
PAST = [1,2,15,27,35,52,57,61,65,69,72,74,75,79,86,93,96,109,120,130,136,150,159,165,207,214,218,235,241,249,268,275,281,290,301,306,311,316,323,324,328,336,337,344,350,351,356,365,371,377,385,389,392,401,405,408,414,436,451,460,468,478,483,497,501,504,508,510,515,519,528,537,545,548,551,556,562,580,590,591,596,598,602,612,613,625,640,648,656,659,668,686,690,693,701,707,713,723,728,748,750,755,762,764,772,780,795,798,813,816,829,840]
for w in PAST:
    if a.words[w]["pos"]=="v": feat(w,tense="past",verb_form="finite")
for w in [21,100,152,179,184,191,194,200,457,466,471,494,533,607,635,669,674,681,757]:
    feat(w,tense="present",verb_form="finite")
for w in [145,154,171,195,262,419,425,428,446,474,609,664,744,804,822]:
    feat(w,verb_form="base")
for w in [62,188,254,317,437,488,570,610,623]:
    feat(w,verb_form="gerund_participle")
for w in [2,75,324,337,351,540,591,598,613,622,846]:
    feat(w,verb_form="past_participle")
for w,aux in [(2,1),(75,74),(324,323),(337,336),(351,350),(591,590),(598,596),(622,621)]:
    feat(w,aspect="perfect",perfect_auxiliary_id=a.anchor(aux),auxiliary_chain=["perfect"])
    feat(aux,auxiliary_selection="past_participle",dependency_relation="auxiliary")
for w,aux in [(62,61),(437,436),(610,609)]:
    feat(w,aspect="progressive",progressive_auxiliary_id=a.anchor(aux),participial_function="progressive_lexical_predicate")
    feat(aux,auxiliary_selection="gerund_participle",dependency_relation="auxiliary")
feat(613,voice="passive",passive_auxiliary_id=a.anchor(612))
feat([171,195,744],mood="imperative",imperative_subject_status="understood_addressee")
feat(702,verb_particle_construction="switch_on",dependency_relation="verbal_particle")
feat(610,scope_operator="figurative_comparison")
feat(623,scope_operator="figurative_comparison")
feat(294,adjective_degree="superlative")
feat([394,531],adverb_degree="comparative")

# Copular properties and their syntactic links.
for cop,head,subject in [(109,110,"e7"),(130,131,"e18"),(179,180,"e23"),(241,242,"e28"),(290,291,"e33"),(344,345,"e20"),(365,367,"e7"),(377,378,"e39"),(405,406,"e38"),(545,546,"e49"),(551,553,"e49"),(669,671,"e3"),(674,677,"e3"),(635,637,"e7")]:
    feat(cop,grammatical_subject_id=subject,predicative_complement_id=a.anchor(head),dependency_relation="copula")
    feat(head,copular_link_id=a.anchor(cop),adjective_position="predicative")

# Determiners, anaphoric substitutes, nominal compounds and explicit modifiers.
for w in [182,534,605]: feat(w,determiner_kind="demonstrative",definiteness="definite",deictic_distance_class="proximal" if w==182 else "distal")
feat(43,determiner_kind="definite_article",definiteness="definite")
feat(44,nominal_ellipsis_license="one_substitute_for_person",antecedent_id="e3")
feat(99,mention_form="demonstrative_pronoun",antecedent_id="e14",evidence=[93,96,97],note="That denotes the seven coins retained as payment, inferred from nine minus two.")
feat(475,nominal_ellipsis_license="one_substitute_for_cake",antecedent_id="e7")
feat(680,kind_antecedent_id="kind_wish",nominal_ellipsis_license="one_substitute_for_wish")
feat([731,733,736],nominal_ellipsis_license="one_substitute_for_slice",partitive_construction=True)
feat(633,nominal_ellipsis_license="one_substitute_for_smile",antecedent_id="e53")
feat(404,referent_kind="event",reference_specificity="situation_bound",lexical_gloss="Everything audible inside the cottage, not all things universally.")
feat([496,509,681],expletive_reference=True,note="Time-identificational it; no arbitrary physical-object antecedent assigned.")
feat(493,grammatical_animacy="human",interrogative_form="subject_wh_question",question_gap_role="subject",question_requested_slot="birthday_information_source")
feat(390,sentence_fragment_type="negative_response_fragment",proposition_polarity="negative",lexical_gloss="No observable response to the first knock, not global nonexistence.")
feat(73,quantifier_binding={"quantifier":"no","variable":"person","restriction":"relevant_people","scope":"s36"},proposition_polarity="negative")
for mod,head,relation in [(4,5,"material"),(24,25,"occasion"),(38,39,"function"),(112,113,"flavor"),(139,140,"material"),(147,148,"purpose"),(162,163,"material"),(168,169,"function"),(204,205,"time"),(278,279,"material"),(342,343,"material"),(568,569,"location"),(582,583,"contents"),(704,705,"location"),(740,741,"material"),(778,779,"material"),(788,789,"function"),(827,828,"location")]:
    feat(mod,noun_compound_relation=relation,noun_compound_head_id=a.anchor(head),dependency_relation="nominal_modifier")
for w,head in [(8,9),(23,25),(55,56),(88,90),(89,90),(102,103),(116,117),(134,135),(161,163),(167,169),(232,233),(237,238),(244,245),(251,253),(252,253),(259,260),(273,274),(284,285),(294,295),(348,349),(353,354),(381,382),(453,454),(486,487),(524,525),(542,543),(567,569),(577,578),(619,620),(628,629),(632,633),(716,717),(720,721),(739,741),(767,768),(837,839),(838,839),(851,853),(852,853)]:
    feat(w,adjective_position="attributive_prenominal",syntactic_governor_id=a.anchor(head),dependency_relation="adjectival_modifier")
feat([167,252,284,790,838],participial_function="adjectival_modifier")
feat(89,lemma="clink",lexical_gloss="Making light metallic sounds; adjective modifying the coin pile.")
feat(38,lemma="rolling",lexical_gloss="Nominal compound modifier in rolling pin, not an ongoing rolling event.")
feat([112,162,278,778],ontological_type="material_or_substance")
feat([12,13,56,77,245,265,432,525,721],ontological_type="temporal_expression")
feat([47,127,295,332,362,382,480,492,564,645,743],relational_noun_kind="spatial_region_or_part")
feat([186,454,666,673,678,698],ontological_type="abstract_or_event_nominal")
feat(853,referent_kind="kind",generic_reference=True,note="Twig occurs only as a comparison image; no actual twig introduced.")
feat(441,generic_reference=True,referent_kind="kind",evidence=[440,441,442,443,444,445,446,447],note="Generic conditional cake description applied to the proposed doorstep plan, not another actual cake.")

# Dates, chronology and exact quantities.
feat(3,cardinal_value=9,measure_entity_id="e4",counted_domain={"entity_id":"e4","kind":"coin"})
feat(5,quantity_total={"value":9,"unit":"count","domain":"coins","owner_id":"e1"})
feat(12,calendar_day_name="Thursday",time_expression_id="t_story_day",temporal_anchor_unresolved=True)
feat(13,time_expression_id="t_departure_morning",time_anchor_id="t_story_day",temporal_granularity="part_of_day")
feat(55,temporal_deixis="previous_spring",time_expression_id="t_previous_spring")
feat(56,time_expression_id="t_previous_spring",temporal_granularity="season")
feat(70,temporal_deixis="current_day",time_anchor_id="t_story_day",evidence=[12,65,68,70,508,512,514,515,683],note="Whole-story reading: Tessa reports the date using her present today; do not place the current Thursday inside last spring.")
feat(77,temporal_duration={"unit":"year","value":None,"quantification":"plural_unspecified"})
feat(95,temporal_order_cue="subsequently")
feat(97,cardinal_value=2,quantity_part={"part":2,"whole":9,"whole_entity_id":"e4"})
feat(99,quantity_total={"value":7,"domain":"payment_coins","operands":[9,-2],"unit":"count"},evidence=[3,93,96,97],note="Arithmetic payment amount; no denomination or price in money units is inferred.")
feat(105,cardinal_value=1,measure_entity_id="e15")
feat(331,cardinal_value=1,numeral_syntactic_role="nominal_determiner")
feat(263,quantity_fraction_lexeme=0.5,numeral_syntactic_role="measure_fraction")
feat(265,measure_unit="hour",measure_dimension="duration",temporal_duration={"value":0.5,"unit":"hour","kind":"additional_duration"})
feat(266,quantity_comparison_cue="greater",quantity_comparison={"dimension":"duration","difference":0.5,"unit":"hour","left":"e30","right":"e28"})
feat(245,time_expression_id="t_previous_night",time_anchor_id="t_story_day",temporal_deixis="previous_night")
for w in [198,416,811]: feat(w,temporal_deixis="next_day",time_anchor_id="t_story_day")
feat(204,time_expression_id="t_next_morning",time_anchor_id="t_story_day",temporal_deixis="next_morning")
feat(431,temporal_bound_cue="upper_bound")
feat(432,temporal_deadline={"event":E(428),"by":"nightfall","status":"considered_plan_only"})
feat(453,ordinal_rank=3,temporal_iteration_index=3)
feat(697,ordinal_rank=1,temporal_iteration_index=1)
feat(842,cardinal_value=2,measure_entity_id="e68")
feat(577,cardinal_value=1,quantity_exact_value=1,measure_entity_id="e52")
feat(721,time_expression_id="t_story_evening",time_anchor_id="t_story_day",temporal_granularity="part_of_day")
feat([393,438],temporal_frequency_class="repetition")
feat([403,526],temporal_order_cue="subsequently")
feat(785,temporal_deixis="current_narrative_time")
feat([134,348,619],lexical_gloss="Final member of the inscription's letter sequence; last B in HOBB.")

# Physical properties use correlated bundles; simple visual labels use the
# existing legacy attributes field instead of inventing duplicate color keys.
for w,attrs in {4:{"material":"copper"},8:{"color":"blue"},23:{"size":"small"},88:{"size":"small"},89:{"sound":"clinking"},102:{"size":"little"},112:{"flavor":"lemon"},116:{"color":"blue"},121:{"greeting":"happy birthday"},131:{"appearance":"neat"},161:{"width":"broad"},162:{"material":"wicker"},167:{"configuration":"folded"},173:{"orientation":"level"},232:{"age":"old"},237:{"length":"short"},251:{"length":"long"},252:{"surface":"paved"},259:{"length":"long"},273:{"color":"blue"},278:{"material":"paper"},284:{"surface":"paved"},294:{"slope":"steepest"},319:{"orientation":"level"},345:{"decoration_condition":"smudged"},353:{"color":"blue"},381:{"width":"thin"},486:{"color":"gray"},524:{"duration":"long_unspecified"},542:{"age":"old"},546:{"evaluation":"good"},553:{"color_variety":"colorful"},567:{"size":"small"},628:{"size":"big","scope":"negated"},632:{"authenticity":"real"},637:{"evaluation":"fine"},671:{"age":"too_old_for_wishes","source":"Hobb_claim"},677:{"age_suitability":"right_for_wish","source":"Tessa_claim"},716:{"brightness":"bright"},720:{"weather":"rainy"},730:{"shape":"uneven"},732:{"height":"tall"},734:{"thickness":"thin"},739:{"portion":"whole_flower"},767:{"size":"little"},778:{"material":"wicker"},790:{"configuration":"folded"},830:{"visual_tone":"warm"},832:{"color":"gold"},837:{"color":"blue"},838:{"covering":"icing"},851:{"size":"tiny"},852:{"color":"silver"}}.items():
    feat(w,attributes=[{"name":k,"value":v} for k,v in attrs.items()])
world(110,"object_shape","e7","round")
world(136,"spatial_contact","e19",{"touches":"e20"})
world(165,"containment_direct","e22",{"container":"e21"})
world(173,"spatial_orientation","e21",{"orientation":"level"},status="directive")
world(180,"object_surface_condition","e23","uneven",status="reported")
world(188,"object_stability","e21",{"condition":"carrier_rushes","risk":"tip"},status="conditional")
world(207,"containment_transitive","e7",{"container":"e21","via":"e37"},evidence=[207,209,212,340,582,583],note="Later cake-box mention resolves the earlier packaging retrospectively; no unmentioned box insertion event is fabricated.")
world(212,"possession_borrower","e21",{"borrower":"e1"},evidence=[145,148,159,163,195,196,207,212],note="Loan uptake inferred from handing over the prepared basket and subsequent actual use, not from the question alone.")
world(212,"possession_lender","e21",{"lender":"e2"})
world(212,"transfer_return_due","e21",{"due_condition":"tomorrow","purpose_context":"morning_loaves","source_id":"e2"},status="instructed")
world(216,"possession_holder","e21",{"holder":"e1"})
world(219,"motion_speed_class","e1","slow")
world(235,"motion_stopping_location","e1",{"stopped_at":"e27"})
world(242,"object_surface_condition","e28","muddy")
world(242,"causal_parent","e28",{"cause":"e29","effect":"muddy"},evidence=[242,243,244,245,246],note="The from-phrase explicitly supplies the rain as cause of mud.")
world(254,"spatial_configuration","e30",{"relation":"winds_around","landmark":"e31"})
world(281,"motion_route","e1",{"role":"route","landmark_id":"e30","event_id":E(281)})
world(291,"object_surface_condition","e33","lumpy")
world(311,"motion_collision","e21",{"collided_with":"e36"})
world(317,"spatial_orientation","e21",{"orientation":"level"})
world(337,"spatial_contact","e7",{"touches":"e37","part":"corner"})
world(345,"object_surface_condition","e20","smudged")
world(351,"event_state_change","e19",{"before":"recognizable_B","after":"blue_squiggle"})
world(367,"object_integrity","e7","intact")
world(371,"motion_arrival_completion","e1",{"arrived_at":"e38"})
world(378,"object_openness","e39","closed")
world(385,"spatial_configuration","e40",{"relation":"beneath","landmark":"e39"})
world(406,"object_sound_level","e38","quiet_after_creak")
world(446,"object_integrity","e7",{"would_remain_whole":False,"condition":"left_outside_in_drizzle"},status="hypothetical")
world(478,"object_openness","e45","ajar")
world(488,"spatial_orientation","e46",{"orientation":"upward","region":"back_of_head"})
world(528,"object_openness","e45","wider_open")
world(539,"bridging_relation","e48",{"anchor":"e10","relation":"part_of"},status="reported")
world(540,"material_composition","e48",{"components":"e49"},status="remembered")
world(556,"motion_boundary_crossing","e1",{"boundary":"e45","crossed":True})
world(580,"containment_direct","e37",{"container":None,"removed_from":"e21"})
world(591,"spatial_orientation","e7",{"orientation":"slightly_tilted"})
world(598,"object_integrity","e7","not_fallen_apart")
world(640,"spatial_region","e15",{"region":"center","landmark":"e7"})
world(659,"object_luminosity","e15","lit")
world(693,"object_luminosity","e15","unlit")
world(693,"causal_parent","e15",{"cause":E(690),"effect":E(693)},evidence=[690,692,693,694,697,698],note="Immediate blow/extinguish sequence and first-try wording support this local physical relation.")
world(701,"object_luminosity","e59","on")
world(707,"object_openness","e39","open")
world(713,"access_visibility","e60",{"visible":True,"appearance":"bright_square"})
world(723,"event_state_change","e7",{"before":"whole_cake","after":"cut_into_slices"})
world(762,"transfer_recipient_acceptance","e64",{"recipient":"e3","accepted":True})
world(780,"spatial_configuration","e21",{"relation":"beside","landmark":"e66"})
world(784,"containment_contents","e21",{"contents":["e22"],"excluded_contents":["e7","e37"]},evidence=[580,583,587,779,784,789,792],note="Empty now means emptied of cake/box; the immediately following towel explicitly remains inside. Do not encode absolutely empty.")
world(790,"containment_direct","e22",{"container":"e21"})
world(798,"motion_collectivity","e3",{"companions":["e1"],"coordination":"accompaniment_to_gate"})
world(804,"possession_return_target","e21",{"return_to":"e2"},status="promised")
world(822,"event_collective_participants","e21",{"actors":["e1","e3"]},status="proposed")
world(829,"object_luminosity","e60","glowing_from_lit_kitchen")
world(840,"spatial_configuration","e7",{"relation":"between","landmark":"e68"})
world(846,"spatial_configuration","e15",{"relation":"beside","landmark":"e7"})

# A few definite parts are linked to their whole, without treating holder as owner.
for w,anchor in [(39,"e2"),(117,"e7"),(129,"e7"),(135,"e18"),(140,"e7"),(216,"e21"),(305,"e34"),(314,"e1"),(376,"e38"),(487,"e3"),(539,"e10"),(569,"e38"),(655,"e54"),(661,"e15"),(688,"e3"),(705,"e38"),(712,"e38"),(783,"e1"),(802,"e38")]:
    feat(w,bridging_relation={"anchor":anchor,"relation":"associated_part_or_fixture"})
feat(4,material_composition=bundle("e4","copper",4))
feat(162,material_composition=bundle("e21","wicker",162))
feat(278,material_composition=bundle("e32","paper",278))
feat(53,possession_owner=bundle("e10",{"owner":"e1"},53))
feat(462,reference_metonymic_link={"intended_speaker_id":"e3","relation":"voice_for_speaker"},evidence=[455,460,462,481,482,493,499],note="Later entrance and dialogue resolve the initially unnamed voice to Hobb.")

# Adverbial meanings and event attachment remain local.
for w,governor,manner in [(98,96,"return_direction"),(156,154,"carefully"),(197,195,"return_direction"),(219,218,"slowly"),(302,301,"passing"),(325,324,"away"),(359,356,"gently"),(360,356,"restore_previous_position"),(394,392,"louder"),(443,442,"outside"),(469,468,"response"),(484,483,"outward"),(489,488,"upward"),(516,515,"return"),(531,528,"wider"),(584,580,"outward"),(593,591,"small_degree"),(599,598,"separation"),(694,693,"extinguishment"),(729,728,"result"),(773,772,"softly"),(791,790,"neatly"),(792,790,"inside_basket"),(807,804,"return_direction")]:
    feat(w,syntactic_governor_id=a.anchor(governor),dependency_relation="adverbial_modifier",lexical_gloss=manner)
feat([366,634],discourse_relation_kind="persistence_despite_concession")
feat(286,discourse_relation_kind="unexpected_persistence",discourse_concession_target="p12")
feat(369,temporal_order_cue="eventual_arrival")
feat(449,temporal_duration={"qualitative":"long","scope":"negated_duration"})
feat(552,lexical_gloss="Degree intensifier of colorful",syntactic_governor_id=a.anchor(553))
feat(670,lexical_gloss="Excess relative to eligibility for wishes, according to Hobb",syntactic_governor_id=a.anchor(671))
feat(675,lexical_gloss="Emphatic exact suitability, not a numeric age",syntactic_governor_id=a.anchor(677))
feat(760,discourse_relation_kind="result",discourse_result_target="p21")
feat(819,discourse_relation_kind="responsive_plan_revision")

# Polarity, attribution and mental/narrative interpretations.
feat(75,negation_scope_id="p4",proposition_polarity="negative",belief_holder_id="e3",evidence_report_depth=2,evidence_explicit=True)
feat(194,negation_scope_id="p7",proposition_polarity="negative",promise_content_id="p7",speaker_id="e1",addressee_ids=["e2"],plan_commitment_status="promised")
feat(445,negation_scope_id="p16",proposition_polarity="negative")
feat(457,negation_scope_id="p17",proposition_polarity="negative",goal_owner_id="e3",goal_content_id="p18",goal_status="explicitly_not_desired",evidence=[455,456,457,459],note="Negated desire is not an active avoidance goal; the desired-state candidate is having cake, not the reporting act.")
feat(597,negation_scope_id="p14",proposition_polarity="negative")
feat(626,negation_attachment_kind="NP_modifier",lexical_gloss="Negates big, not the existence of the smile.")
prop("p29","The basket's carrier rushes.",[190,191],"s37")
feat(189,scope_operator="conditional",conditional_antecedent_id="p29",conditional_consequent_id="p6")
feat(21,goal_owner_id="e1",goal_content_id="p1",goal_beneficiary_ids=["e3"],intention_publicity="communicated")
feat(152,goal_owner_id="e1",goal_content_id="p5",goal_resource_ids=["e21"],goal_status="active",intention_publicity="communicated")
feat(188,warning_hazard_id="p6",speaker_id="e2",addressee_ids=["e1"])
feat(195,obligation_debtor_id="e1",obligation_creditor_id="e2",obligation_content_id="p8",obligation_status="instructed",goal_deadline={"anchor":"next_day","relation":"during","purpose_context":"morning_loaves"})
prop("p30","The basket is available to Mrs. Pike for the next morning's loaves.",[199,200,201,204,205],"s12")
feat(200,goal_owner_id="e2",goal_content_id="p30")
feat(281,goal_owner_id="e1",goal_content_id="p5",goal_tradeoff={"prefer":"protect_cake","accept_cost":"p11","holder_id":"e1","assertion_status":"candidate"},evidence=[242,249,260,262,268,271,281],note="Narrative juxtaposition supports this practical choice as an interpretation; no explicit inner speech or emotion is invented.")
feat(419,reasoner_id="e1",reasoning_mode="plan_consideration",reasoning_content_id="p15",plan_step_ids=[E(419),E(425),E(428)],plan_commitment_status="considered_not_adopted",evidence=list(range(417,450)),note="Free indirect planning; later knock shows the leave-cake branch is not executed.")
feat(446,reasoner_id="e1",mental_simulation_outcome="p16",reasoning_premise_ids=["p15"],evidence=[419,421,424,435,437,440,441,445,446,447],note="Prediction within considered plan, not an observed ruined cake.")
feat(451,narrative_thread_id="thread_cake_delivery",narrative_thread_status="pursued",evidence=[419,425,428,446,450,451],note="Third knock demonstrates continued engagement instead of the contemplated departure.")
feat(466,knowledge_claim_holder_id="e1",knowledge_claim_content_id="p17",epistemic_source_kind="testimony",epistemic_source_entity_id="e3",belief_polarity="accepts",evidence=[455,456,457,465,466],note="Acknowledges his stated non-desire; does not claim omniscient access to hidden feelings.")
feat(471,goal_owner_id="e1",goal_content_id="p18",goal_beneficiary_ids=["e3"],goal_polarity="achieve",intention_publicity="communicated")
feat(533,mental_memory_holder_id="e3",mental_memory_content_id="p19",mental_memory_event_id=E(52),evidence=[52,54,503,504,506,532,533,535],note="Same kite-repair episode, not a new repair. Sock-tail details are remembered content.")
feat(546,viewpoint_evaluative_stance={"holder_id":"e1","target":"e49","stance":"good"})
feat(553,viewpoint_evaluative_stance={"holder_id":"e3","target":"e49","stance":"colorful"},note="Potential tactful humor is left open; colorful does not logically mean bad.")
feat(610,figurative_mapping={"target_id":"e20","source_image":"swimming","kind":"metaphor","literal_event":False},evidence=[343,345,605,606,607,610],note="Smudged decoration is described playfully; no swimming organism is introduced.")
feat(623,figurative_mapping={"target_id":"e19","source_image":"wandering","kind":"metaphor","literal_event":False},evidence=[349,351,354,619,620,622,623],note="Changed letter shape/location, not an autonomous travel event.")
feat(625,affect_experiencer_id="e3",affect_expression_channel="smile",affect_display_authenticity="explicitly_genuine",evidence=[624,625,626,628,629,632,633],note="The text calls the smile real. Specific internal emotions or intensity beyond the stated small display remain unassigned.")
feat(637,viewpoint_evaluative_stance={"holder_id":"e3","target":"e7","stance":"fine_despite_damage"},discourse_concession_target="p13")
feat(671,belief_holder_id="e3",belief_content_id="p23",belief_polarity="accepts")
feat(677,belief_holder_id="e1",belief_content_id="p24",epistemic_disagreement_parties=["e1","e3"],discourse_correction_target="p23")
feat(690,note="Blowing out the candle is explicit. The text never states that Hobb silently makes a wish, so no fulfilled wish event is added.",evidence=[662,664,669,671,674,677,686,690])
feat(804,promise_content_id="p26",speaker_id="e3",addressee_ids=["e1"],plan_commitment_status="promised",intention_publicity="communicated")
feat(818,obligation_debtor_id="e1",obligation_creditor_id="e2",obligation_content_id="p8",obligation_status="acknowledged")
feat(822,cooperation_goal_id="p27",social_relation_participants={"members":["e1","e3"]},cooperation_commitment="proposed_by_Hobb",plan_revision={"old":"p26","new":"p27"},evidence=[803,804,811,814,815,816,817,818,819,820,821,822],note="Hobb changes solo offer to joint return; Tessa's acceptance and the next-day return are not narrated.")
feat(829,narrative_motif_link={"earlier":"p28:closed_curtains","current":"p28:bright_window","relation":"contrasted_return"},narrative_change_dimension="visible_house_openness_and_shared_birthday",evidence=[378,385,707,713,717,763,764,828,829],note="Retrospective narrative interpretation anchored in physical states; not a diagnosis of Hobb's prior loneliness.")
feat(839,narrative_closure_candidate={"cue":"final_shared_cake_image","thread":"thread_cake_delivery","status":"candidate"},narrative_resolution_evidence={"problem":"p18","outcome":"p25","status":"delivery_and_sharing_observed"},evidence=[470,471,472,475,763,764,839,843],note="Sharing closes the delivery thread. The basket-return commitment remains future and unfulfilled in the story.")
feat(849,figurative_mapping={"target_id":"e15","source_image":"tiny silver twig","kind":"simile","literal_identity":False},evidence=[845,846,849,851,852,853],note="The candle remains a candle; silver is visual description, not proof of metal composition.")

# Reuse visible communication events where a reporting clause provides one.
# Otherwise create a secondary actual speech event, separate from the content.
TURN_REPORT = {"s1":27,"s2":27,"s4":57,"s5":57,"s7":120,"s8":150,"s9":150,"s14":460,"s15":468,"s16":468,"s20":548,"s26":668,"s29":748,"s30":755,"s31":755,"s32":813}
ACTS = {"s1":"request","s2":"recipient_specification","s3":"clarification_question","s4":"explanation","s5":"report","s6":"price_statement","s7":"inscription","s8":"permission_request","s9":"intention_statement","s10":"instruction_and_warning","s11":"commitment","s12":"return_instruction","s13":"self_identification","s14":"refusal","s15":"acknowledgment","s16":"goal_statement","s17":"information_question","s18":"answer_and_reminder","s19":"memory_report","s20":"evaluation","s21":"evaluation","s22":"playful_description","s23":"explanation","s24":"playful_description","s25":"positive_evaluation","s26":"suggestion","s27":"objection","s28":"reassurance","s29":"offer","s30":"explanation","s31":"counteroffer","s32":"offer_and_commitment","s33":"reported_obligation","s34":"joint_plan_proposal"}
for sid,start,stop,speaker in QUOTES:
    audience="e2" if int(sid[1:])<=12 and speaker=="e1" else "e1" if speaker in {"e2","e3"} else "e3"
    if sid=="s7":
        audience="e3"  # The written birthday greeting explicitly addresses Hobb.
    if sid in TURN_REPORT:
        utterance=E(TURN_REPORT[sid])
    else:
        N+=1; utterance=f"ev{N}"
        a.event(utterance,start,ACTS[sid],type="speak",actor=speaker,recipient=audience,
                scope="s0",factuality="asserted",primary=False,support=list(range(start,stop)))
    a.scopes[sid]["utterance_event_id"]=utterance
    a.scopes[sid]["addressee_ids"]=[audience]
    feat(start,utterance_id=utterance,speech_act_kind=ACTS[sid],speaker_id=speaker,
         addressee_ids=[audience],communication_channel="writing" if sid=="s7" else "speech",quote_mode="direct_quotation")
    if sid=="s7":
        # Structural quotation scope marks the inscription span; its channel is writing.
        feat(start,quote_mode="written_inscription")

# Replace the provisional final report record with a mention of the original
# instruction. The actual evening Tessa reporting turn remains separate.
old_instruction=EVENT_AT[816][0]
original_instruction=a.scopes["s12"]["utterance_event_id"]
for r in a.words:
    r["event_bindings"]=[b for b in r.get("event_bindings",[]) if b["event_id"]!=old_instruction]
    if not r["event_bindings"]:
        r.pop("event_bindings")
    if r.get("event_id")==old_instruction:
        for key in ["event_id","event","role","actor","actor_id","recipient_id","patients","instruments","event_type","factuality"]:
            r.pop(key,None)
a.events.pop(old_instruction)
a.mention_event(original_instruction,816,role="action",note="Tessa reports the earlier Pike instruction.")
a.mention_event(original_instruction,[814,815],role="actor")
EVENT_AT[816]=[original_instruction]
feat(816,event_antecedent_id=a.scopes["s12"]["utterance_event_id"],evidence_report_depth=1)
for w,scope,content in [(20,"s1","p1"),(51,"s4","p2"),(59,"s5","p3"),(151,"s9","p5"),(192,"s11","p7"),(195,"s12","p8"),(455,"s14","p17"),(465,"s15","p17"),(470,"s16","p18"),(532,"s19","p19"),(662,"s26","p22"),(669,"s27","p23"),(674,"s28","p24"),(803,"s32","p26"),(814,"s33","p8"),(819,"s34","p27")]:
    feat(w,utterance_content_id=content)
feat(500,dialogue_response_to_id=a.scopes["s17"]["utterance_event_id"],dialogue_turn_function="answer",question_answer_status="answered_by_original_teller")
feat(465,dialogue_response_to_id=a.scopes["s14"]["utterance_event_id"],dialogue_turn_function="acknowledgment")
feat(814,dialogue_response_to_id=a.scopes["s32"]["utterance_event_id"],dialogue_turn_function="obligation_reminder")
feat(819,dialogue_response_to_id=a.scopes["s33"]["utterance_event_id"],dialogue_turn_function="joint_plan_revision")

# Scoped assertion labels are written only on predicates/operators, never copied
# as a physical state or emotion across an entire sentence.
for event in a.events.values():
    w=event["trigger"]
    if a.words[w].get("event_id")==event["event_id"]:
        feat(w,assertion_status="asserted" if event["scope_id"]=="s0" else "attributed_claim",
             supporting_mention_indices=event["support_words"])
# Syntactic subjects are explicitly listed, not copied wholesale from actor.
for entity,words in {
 "e1":[2,15,27,57,79,145,150,152,154,194,207,214,218,235,249,268,281,316,317,328,356,371,389,392,408,419,425,428,451,466,468,471,548,556,580,640,668,750,755,795],
 "e2":[35,93,96,120,159,165,200,414,816],
 "e3":[52,62,65,72,457,460,474,483,494,501,504,508,519,528,533,562,570,602,625,648,659,686,690,701,707,723,748,757,762,798,804,813],
 "e14":[100],"e34":[301,324],"e35":[306],"e21":[311],"e47":[515],"e65":[764,822],
}.items():
    feat(words,grammatical_subject_id=entity)
feat([494,501],evidence=[493,494,495,500,501],note="Who asks for the prior teller; the retrospective answer You identifies Hobb. The outer question/answer speech acts are distinct from this old telling.")
for w in [188,191,262,419,425,428,442,446]: feat(w,assertion_status="attributed_claim")
for w in [145,171,195,494,664,744,757,804,822]: feat(w,assertion_status="attributed_claim")
feat(414,factuality="asserted",evidence=[199,200,201,204,205,412,413,414,415,416],note="Narration reactivates the previously quoted basket need; this is the same continuing need, not a new request.")
feat(494,assertion_status="attributed_claim",truth_commitment="suspended")
feat(816,factuality="reported")
for w in [746,759]:
    feat(w,reference_metonymic_link={"literal":"e20","intended":"e64","relation":"decoration_for_decorated_slice"},evidence=[736,739,741,w],note="Flower names the flower-topped slice in this serving exchange; the literal decoration and the transferred slice retain distinct identities.")

# All ordinary pronoun links resolve to the explicit stable mention chains.
for eid,entity in a.entities.items():
    ordered=sorted(entity["mentions"])
    for index,w in enumerate(ordered):
        if a.words[w]["pos"]=="pron" and index:
            feat(w,antecedent_id=eid,reference_chain_id=f"rc_{eid}",antecedent_mention_index=a.words[ordered[index-1]]["index"])
for w in [66,16,521,799,825]:
    feat(w,lemma={66:"I",16:"they",521:"she",799:"she",825:"he"}[w])

# Final morphology review: only finite forms carry morphosyntactic tense.
# A perfect construction may locate an event in the past, but the participle's
# own inflectional form is not a finite past-tense verb.
for w in [2,75,324,337,351,540,591,598,613,622,846]:
    a.words[w].pop("tense",None)
for w in [21,194,249]:
    a.words[w].pop("tense",None)
    feat(w,verb_form="base")
feat(494,tense="past",verb_form="finite")
feat(621,tense="present",verb_form="finite",dependency_relation="auxiliary")
feat(818,verb_form="finite",modal_auxiliary_class="necessity_family")
feat(316,lexical_sense_id="freeze:stop_moving_suddenly",lexical_gloss="Stop moving suddenly; no change of temperature or material phase.")
feat(42,ontological_type="spatial_region",lexical_gloss="Unspecified space above the work surface in which the rolling pin is held.")
feat(186,lexical_gloss="Reported disposition of this basket to tip under the specified condition, not an intentional habit.")
feat(122,lexical_gloss="Birthday named within a written greeting",referential_use="attributive")
feat(264,determiner_kind="indefinite_article",definiteness="indefinite")
feat(447,attributes=[{"name":"integrity","value":"whole"}],adjective_position="predicative",syntactic_governor_id=a.anchor(446))
feat(657,subordinator_type="temporal",temporal_signal_relation="overlap")
feat([20,669,803,820],grammatical_person=1,grammatical_case="nominative")
feat(674,grammatical_person=2,grammatical_case="nominative")
feat([397,635,681],grammatical_person=3,grammatical_number="singular")
feat([472,495],grammatical_case="objective")
for r in a.words:
    if r["pos"]=="pron" and r["token"].casefold()=="it":
        feat(r["word_index"],grammatical_person=3,grammatical_number="singular",mention_form="personal_pronoun")
    if r["pos"]=="pron" and r["token"].casefold() in {"she","her","he","him"}:
        feat(r["word_index"],grammatical_gender="feminine" if r["token"].casefold() in {"she","her"} else "masculine")

FEEDBACK = {
"summary":"Complete manually selected lexical and contextual annotation of the bakery story. Retrospective interpretation is intentional; physical states retain narrated time, quoted content stays attributed, and proposed plans are not promoted to actions.",
"ambiguities":[
 {"words":[65,68,69,70,508,512,514,515],"issue":"Birthday time is reported retrospectively with today and a seasonal swallow cue.","decision":"today anchors to the current Thursday in Tessa's paraphrase; no absolute date, annual migration schedule, or date-consistency repair is invented."},
 {"words":[155,172,196,277,611],"issue":"Repeated it shifts between cake and basket.","decision":"Resolve 155 to cake (purpose of asking for basket), 172/196 to basket, 277 to cake and 611 to cake; 611 could narrowly mean the flower but reported bump targets the transported cake."},
 {"words":[52,62,504,65,508,750],"issue":"Repeated mentions of historical repair, telling and purchase are not repeated physical events.","decision":"Reuse event IDs through mention_event; distinct outer communication turns keep their own IDs."},
 {"words":[546,553,610,623,637],"issue":"Colorful socks and playful decoration descriptions may carry tact or humor.","decision":"Annotate explicit evaluations and clear visual metaphor; do not infer sarcasm, insult or hidden disappointment."},
 {"words":[625,632,693],"issue":"A real smile and blowing out the candle do not explicitly report a wish or a named inner emotion.","decision":"Keep genuine outward display and candle event; omit an invented wish-making event or measured happiness."},
 {"words":[779,784,789,792],"issue":"Empty basket still contains tea towel.","decision":"Record contents towel, excluding cake/box, rather than absolute emptiness."},
 {"words":[804,811,814,818,820,822],"issue":"Final joint return is a proposal; story ends before tomorrow.","decision":"Keep obligation and future commitment, do not assert completed return or Tessa's unstated acceptance."},
],
"feature_gaps":[
 {"field":"figurative_mapping","reason":"Needed for novel swimming/wandering metaphors and candle/twig simile; neither irony nor conventional lexical idiom fits.","words":[610,623,849]},
 {"field":"attributes","reason":"The catalog has many specialized material/state fields but no ordinary typed color/size/flavor field; retained legacy name/string values for blue, small and lemon. A future common property schema would improve consistency.","words":[8,23,112,116,162,837]},
 {"field":"event_bindings","reason":"Multiple event memberships and speaker/content overlap need the provisional array; singular fields cannot represent all roles.","words":[190,192,195,662,669,803,820]},
],
"prompt_feedback":[
 "Specify event identity versus event mention identity, including repeated descriptions across quotation scopes; reuse underlying physical events and allocate distinct actual speech acts.",
 "Keep the newly clarified patients/instruments ID override visible alongside the original feature descriptions, which otherwise prescribe names.",
 "Distinguish actual utterance event scope from its quoted content scope; secondary speech events can share a word anchor without replacing content participants.",
 "Give a scoped-emptiness example such as empty basket with towel still inside, so annotations do not infer universal absence.",
 "Keep the shared leading-component contraction policy visible: this pilot uses pron/I for I'd and I'm, pron/you for You're, pron/it for It's, with full auxiliary expansions; won't and don't remain verbal contractions.",
 "Time expressions need a policy for reported deictic reformulation: today in a present retelling of last spring's conversation need not mean that historical conversation day.",
 "Narrative closure and character change should cite physical evidence and remain interpretations, without turning smile/light imagery into unsupported psychiatric or personality claims.",
],
"coverage_notes":"All 854 word occurrences have explicit contextual POS; every inflected/proper-name/contraction lemma was reviewed. Events, pronouns, quotations, conditions, object parts, route choice, decorations, cake integrity, arithmetic and loan commitments were reviewed paragraph by paragraph. Function words receive grammar/operator labels where appropriate; omissions remain unknown, not false. Full dependency trees and all 1,024 dimensions are deliberately not fabricated.",
"reviewed_all_words":True,
}
a.save(FEEDBACK)
