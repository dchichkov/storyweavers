#!/usr/bin/env python3
"""
A standalone storyworld for a tiny comedy about photography, a twit, and an aster.

The premise:
- A child photographer wants a picture of a prized aster.
- A fictional twit-bird keeps interrupting the shot.
- Kindness and a small transformation turn the trouble into a silly helper.

The world model tracks:
- physical meters: ready, tangled, bright, muddy, moved, snapped
- emotional memes: joy, annoyance, worry, kindness, shame, pride, laughter

The story is generated from a simulated causal world so the prose reflects
what changed, not a fixed template with swapped nouns.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402

ENTITY_HUMAN = "human"
ENTITY_ANIMAL = "animal"
ENTITY_OBJECT = "object"


@dataclass
class Entity:
    id: str
    kind: str = ENTITY_OBJECT
    type: str = ENTITY_OBJECT
    label: str = ""
    phrase: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    location: str = ""

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == ENTITY_HUMAN:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == ENTITY_ANIMAL:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    setting: str
    hero: str
    twit: str
    aster: str
    scenario: str = "reflection"
    opening_style: int = 0
    comic_beat: int = 0
    kindness_style: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    premise: str
    trouble: str
    clue: str
    first_try: str
    need: str
    kind_action: str
    invitation: str
    helpful_action: str
    photo: str
    ending: str
    lesson: str


SETTINGS = {
    "garden": "the garden",
    "greenhouse": "the greenhouse",
    "park": "the park",
    "backyard": "the backyard",
}

HERO_NAMES = ["Mina", "Lola", "Nia", "Poppy", "Tia", "June", "Ivy"]
TWIT_NAMES = ["Tib", "Nip", "Zip", "Murm", "Wren"]
ASTER_NAMES = ["aster", "purple aster", "starry aster", "blue aster"]

SCENARIOS = {
    "reflection": Scenario(
        premise="wanted to catch the morning dew shining like beads on its petals",
        trouble="fluttered a silver wrapper beside the flower, throwing a white glare across every picture",
        clue="noticed the bird kept tilting the wrapper toward a dark patch beneath the hedge",
        first_try="held up a hat to block the glare, but the hat's shadow covered the aster too",
        need="was trying to send a bright signal to a lost fledgling under the hedge",
        kind_action="set a little hand mirror on the path so the signal could continue away from the flower",
        invitation="Keep your signal, and help me aim this gentler one",
        helpful_action="angled the mirror with one wing until the fledgling chirped back",
        photo="the dew-lit aster, the small mirror, and two reunited twit-birds",
        ending="A round drop of dew held all three upside down in its tiny shining world.",
        lesson="Kindness begins by asking what a troublesome action is trying to accomplish.",
    ),
    "wind": Scenario(
        premise="planned a stop-motion sequence of the aster slowly opening",
        trouble="dragged a broad leaf through the frame, making a gust that bent the flower",
        clue="heard a dry nest scrape whenever the leaf stopped moving",
        first_try="weighted the tripod with a pebble, but the aster still nodded out of view",
        need="needed to fan a hot nest where three chicks were panting",
        kind_action="folded a paper fan and moved the nest into the cool shade with the gardener's help",
        invitation="Your breeze matters; let's point it where it helps",
        helpful_action="fanned the chicks softly, then held the leaf behind the aster as a green backdrop",
        photo="the open aster framed by a leaf while three cooled chicks peeked over its edge",
        ending="The last frame showed one petal opening as three tiny beaks opened in a matching yawn.",
        lesson="A good solution protects the picture and the living creatures around it.",
    ),
    "pollen": Scenario(
        premise="hoped to photograph a bee landing on the star-shaped bloom",
        trouble="sneezed so explosively that the bee fled and the camera strap landed over the lens",
        clue="saw yellow pollen dusting the bird's beak after every sneeze",
        first_try="whispered 'hold it in,' which only produced an even bigger achoo",
        need="was sensitive to the loose pollen beside the camera",
        kind_action="offered a clean damp leaf and moved the tripod upwind",
        invitation="You don't have to stop sneezing; you can warn me before the next one",
        helpful_action="raised one wing before each sneeze so the shutter could click between them",
        photo="a bee balanced on the aster while the twit-bird saluted with its warning wing",
        ending="The bee flew off just as a final sneeze puffed one harmless yellow ring through the sunlight.",
        lesson="Kindness makes room for needs people and creatures cannot simply switch off.",
    ),
    "shadow": Scenario(
        premise="wanted a silhouette of the aster at sunset",
        trouble="kept hopping onto the low wall and turning the flower's neat shadow into a lumpy crown",
        clue="realized the bird was copying every pose the child's shadow made",
        first_try="waved it away, but the waving shadow looked like an invitation to dance",
        need="wanted to join the game and did not understand the careful setup",
        kind_action="marked a special posing spot with a chalk star beside the flower's shadow",
        invitation="This star is your place in the picture",
        helpful_action="stood on the chalk mark and stretched its wings into a perfect comic bow",
        photo="an aster-shaped shadow beside a bowing bird-shaped shadow",
        ending="On the wall, flower and bird seemed to take one final bow together.",
        lesson="Clear, welcoming directions work better than an angry wave.",
    ),
    "raindrop": Scenario(
        premise="waited through a shower to photograph raindrops on the aster",
        trouble="shook its soaked feathers over the lens until every image became a watery blur",
        clue="noticed the shivering bird had nowhere dry to perch",
        first_try="wiped the lens with a sleeve, then fogged it with a worried breath",
        need="was cold and frightened by a rumble of thunder",
        kind_action="made a dry perch beneath the camera cloth and waited beside it until the thunder passed",
        invitation="Warm up here; when you're ready, you can uncover the lens",
        helpful_action="lifted the cloth at the quiet moment and stayed snug on the perch",
        photo="the rain-jeweled aster reflected in one enormous drop with a dry twit-bird beyond it",
        ending="One raindrop slid from the petal exactly as the shutter gave its soft click.",
        lesson="Pausing to offer safety can save both a friendship and a photograph.",
    ),
    "label": Scenario(
        premise="was making a picture guide so younger children could recognize an aster",
        trouble="stole the plant label and planted it upside down directly in front of the bloom",
        clue="found a trail of mixed-up labels leading toward an empty nest box",
        first_try="replaced the label, but the bird whisked it away again",
        need="was collecting flat sticks to repair a loose nest-box floor",
        kind_action="brought safe fallen twigs and showed which labels had to stay with the plants",
        invitation="Use these twigs for your floor, and carry this blank stick for my picture",
        helpful_action="held the blank stick like a tiny clapboard while the correct label remained in the soil",
        photo="the labeled aster and the twit-bird snapping the blank clapboard shut",
        ending="The bird clacked the stick once more, and everyone called, 'Aster, take two!'.",
        lesson="Sharing the right material can end a conflict without shaming anyone.",
    ),
    "mud": Scenario(
        premise="needed a clean close-up for the garden club calendar",
        trouble="skidded through a puddle and printed muddy footprints across the pale petals",
        clue="spotted a trapped worm twisting in the sticky edge of the puddle",
        first_try="dabbed at a petal too quickly and smeared the mud into a brown moustache",
        need="had rushed through the mud to free the worm",
        kind_action="used a broad leaf to lift the worm and a gentle watering can to rinse the flower",
        invitation="Next time call me; four careful hands and wings are better than a muddy dash",
        helpful_action="held the leaf steady while clean water carried the last mud away",
        photo="the rinsed aster, the rescued worm, and one muddy footprint left on a stone",
        ending="In the calendar picture, the footprint looked exactly like a tiny chocolate flower.",
        lesson="A messy mistake can come from a kind purpose, and kindness can repair it carefully.",
    ),
    "web": Scenario(
        premise="was testing a macro lens on the aster's curling center",
        trouble="pulled a spider thread across the lens and made every bright point stretch into a stripe",
        clue="followed the thread to a web sagging between two stems",
        first_try="pinched the thread away, but the whole web trembled dangerously",
        need="was trying to brace the web before the next breeze",
        kind_action="placed two forked twigs nearby and asked the spider before moving the loose anchor",
        invitation="Hold this end, and we'll keep the web out of the camera's path",
        helpful_action="carried the loose strand to a forked twig without tangling it",
        photo="the aster in crisp focus with a silver web sparkling safely behind it",
        ending="A spider crossed the web as the twit-bird proudly pretended to direct traffic.",
        lesson="Careful cooperation can protect work that is easy to overlook.",
    ),
    "seed": Scenario(
        premise="wanted to record the aster before its last petals fell",
        trouble="plucked at the drying center and sent fuzzy seeds across the frame",
        clue="watched the bird tuck every seed into cracks in a bare corner of the garden",
        first_try="chased the fluff with a butterfly net and caught only the child's own hat",
        need="was planting a future patch of flowers, though its hurried pecks harmed the bloom",
        kind_action="showed how to collect only loose ripe seeds in a paper packet",
        invitation="Let's leave this flower standing and plant the seeds already ready to travel",
        helpful_action="sorted the loose seeds into the packet and patted soil over a new bed",
        photo="the aging aster beside a packet marked NEXT SPRING and a soil-smudged twit-bird",
        ending="One escaped seed settled on the bird's head like a soft white party hat.",
        lesson="Thinking about tomorrow includes caring for what is still alive today.",
    ),
    "lenscap": Scenario(
        premise="arranged a funny portrait with the aster appearing larger than the garden shed",
        trouble="snatched the lens cap and rolled it downhill like a black wheel",
        clue="heard a frightened beetle rattling inside the cap whenever it stopped",
        first_try="ran after it and slipped onto a soft heap of leaves",
        need="was using the rolling cap to carry the beetle away from a busy path",
        kind_action="offered a matchbox with air holes as a safer beetle carriage",
        invitation="Return my cap, and you may be the carriage conductor",
        helpful_action="escorted the beetle to a quiet log and brought the lens cap back",
        photo="the aster towering by perspective over the twit-bird's tiny beetle carriage",
        ending="The beetle raised both feelers from the log as though approving the enormous flower.",
        lesson="Before judging odd behavior, look closely for the small life it may be protecting.",
    ),
    "sign": Scenario(
        premise="was photographing the aster for a KEEP TO THE PATH sign",
        trouble="stood in front of the camera and mimicked every serious pose with an absurd expression",
        clue="noticed visitors laughing, slowing down, and finally seeing the crushed plants near the path",
        first_try="asked for a serious face, which made the bird cross its eyes even harder",
        need="was trying to get distracted walkers to notice the damaged flower bed",
        kind_action="changed the plan and made two photographs: one clear flower and one comic warning",
        invitation="Help me make the path sign impossible to ignore",
        helpful_action="posed beside an arrow while holding both wings away from the fragile bed",
        photo="the bright aster above a comically stern twit-bird pointing toward the safe path",
        ending="The finished sign made visitors grin, then place every foot exactly where it belonged.",
        lesson="Humor becomes helpful when it guides attention instead of stealing it.",
    ),
    "night": Scenario(
        premise="set a long exposure to photograph the aster beneath the first evening stars",
        trouble="blinked a firefly lantern across the frame and drew bright squiggles through the dark image",
        clue="decoded the repeated loops as arrows pointing toward a moth caught in a watering-can handle",
        first_try="covered the lens, which hid the signal and left the moth unseen",
        need="needed help freeing the moth without touching its delicate wings",
        kind_action="tilted the watering can so the moth could crawl out by itself",
        invitation="Flash once when the moth is clear, then paint one star for my picture",
        helpful_action="gave one careful blink after the moth flew and traced a single glowing curve",
        photo="the moonlit aster under a deliberate ribbon of firefly light",
        ending="The moth rested on a petal while one bright curve seemed to tuck the flower into the night.",
        lesson="Patient listening can turn an interruption into useful information and shared art.",
    ),
}

COMIC_BEATS = [
    "The tripod gave a tiny wobble, as if it too were trying not to laugh.",
    "A nearby snail watched with the grave expression of a museum guard.",
    "The camera strap chose that moment to tie itself into a very unhelpful bow.",
    "A robin supplied one questioning chirp, then waited for an explanation.",
    "The gardener's hat fell over one eye at precisely the wrong moment.",
    "Even the watering can seemed to wear its handle like a surprised eyebrow.",
    "A beetle marched past as if inspecting the entire production.",
    "The shutter clicked by accident and captured one excellent picture of a shoe.",
]

KINDNESS_STYLES = [
    "counted three slow breaths before speaking",
    "lowered the camera so they could look at the problem together",
    "remembered that a question could reveal what anger would miss",
    "sat quietly at the bird's height and waited for the flapping to stop",
    "put the precious photograph aside for a moment",
    "named the harm without calling the bird a bad creature",
    "offered help first and instructions second",
    "listened for the reason hidden beneath the commotion",
]

OPENINGS = [
    "{hero} loved photography, especially pictures that helped someone notice a small wonder.",
    "With a camera tucked safely against one hip, {hero} went looking for a wonder small enough to miss.",
    "{hero} believed a careful photograph could make an ordinary garden moment feel important.",
    "The morning's photography plan belonged to {hero}, whose favorite subjects were small, bright, and alive.",
    "Whenever other children hurried past, {hero} paused with a camera and looked twice.",
    "A camera helped {hero} collect moments without picking them or putting them in a jar.",
    "{hero} had learned that good photography begins before the shutter click, with patient looking.",
    "Today's photographic expedition had one member, one camera, and a leader named {hero}.",
]

ASP_RULES = r"""
% A shot is spoiled when the twit is meddling and the aster is not protected.
spoiled(S) :- setting(S), meddles(twit), near(twit, aster), no_protection(aster).

% Kindness can transform the twit into a helper.
helpful(twit) :- kind_action(hero), transformed(twit).

% A reasonable story is one where the twit can be soothed and the aster can still be photographed.
valid_story(S) :- setting(S), spoiled(S), transformed(twit).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    lines.append(asp.fact("meddles", "twit"))
    lines.append(asp.fact("near", "twit", "aster"))
    lines.append(asp.fact("no_protection", "aster"))
    lines.append(asp.fact("kind_action", "hero"))
    lines.append(asp.fact("transformed", "twit"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(SETTINGS.keys())
    cl = set(s for (s,) in asp_valid())
    if py == cl:
        print(f"OK: ASP model covers {len(py)} story settings.")
        return 0
    print("MISMATCH between Python and ASP setting coverage.")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Photography, twit, and aster comedy storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hero")
    ap.add_argument("--twit")
    ap.add_argument("--aster")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice(HERO_NAMES)
    twit = args.twit or rng.choice(TWIT_NAMES)
    aster = args.aster or rng.choice(ASTER_NAMES)
    return StoryParams(
        setting=setting,
        hero=hero,
        twit=twit,
        aster=aster,
        scenario=rng.choice(list(SCENARIOS)),
        opening_style=rng.randrange(len(OPENINGS)),
        comic_beat=rng.randrange(len(COMIC_BEATS)),
        kindness_style=rng.randrange(len(KINDNESS_STYLES)),
    )


def _should_reject(params: StoryParams) -> Optional[str]:
    if params.hero.lower() == params.twit.lower():
        return "The hero and the twit need different names so the comedy can clearly land."
    return None


def build_world(params: StoryParams) -> World:
    err = _should_reject(params)
    if err:
        raise StoryError(err)

    world = World(SETTINGS[params.setting])

    hero = world.add(Entity(
        id="hero",
        kind=ENTITY_HUMAN,
        type="child",
        label=params.hero,
        phrase=f"the child photographer {params.hero}",
        memes={"joy": 1.0, "kindness": 0.0, "worry": 0.0, "laughter": 0.0},
    ))
    twit = world.add(Entity(
        id="twit",
        kind=ENTITY_ANIMAL,
        type="twit-bird",
        label=params.twit,
        phrase=f"a little fictional twit-bird named {params.twit}",
        meters={"mess": 0.0, "moved": 0.0, "bright": 0.0},
        memes={"annoyance": 1.0, "shame": 0.0, "pride": 0.0},
        location="bushes",
    ))
    aster = world.add(Entity(
        id="aster",
        kind=ENTITY_OBJECT,
        type="flower",
        label=params.aster,
        phrase=f"a bright {params.aster}",
        meters={"bright": 1.0, "ready": 1.0, "snapped": 0.0},
        location="sunny patch",
    ))
    camera = world.add(Entity(
        id="camera",
        kind=ENTITY_OBJECT,
        type="camera",
        label="camera",
        phrase="a small camera",
        owner=hero.id,
        meters={"ready": 1.0},
    ))

    world.facts.update(
        params=params,
        scenario=SCENARIOS[params.scenario],
        hero=hero,
        twit=twit,
        aster=aster,
        camera=camera,
        obstacle_seen=False,
        need_understood=False,
        repaired=False,
    )
    return world


def predict_shot(world: World) -> dict:
    sim = world.copy()
    twit = sim.get("twit")
    aster = sim.get("aster")
    spoiled = twit.location == "beside the aster" and twit.meters.get("mess", 0.0) >= 1.0
    if spoiled:
        aster.meters["ready"] = 0.0
    return {"spoiled": spoiled, "bright": aster.meters.get("bright", 0.0)}


def act_setup(world: World) -> None:
    hero = world.get("hero")
    aster = world.get("aster")
    scenario = world.facts["scenario"]
    world.say(OPENINGS[world.facts["params"].opening_style].format(hero=hero.label))
    world.say(f"For today's photography in {world.setting}, {hero.pronoun('subject')} found {aster.phrase} and {scenario.premise}.")


def act_twit_interrupts(world: World) -> None:
    twit = world.get("twit")
    aster = world.get("aster")
    hero = world.get("hero")
    scenario = world.facts["scenario"]
    twit.location = "beside the aster"
    twit.meters["mess"] = 1.0
    hero.memes["worry"] = 1.0
    world.facts["obstacle_seen"] = True
    world.say(f"Then {twit.phrase} {scenario.trouble}.")
    world.say(f"{hero.label} tried once to rescue the shot: {hero.pronoun('subject')} {scenario.first_try}.")
    world.say(COMIC_BEATS[world.facts["params"].comic_beat])


def act_kindness(world: World) -> None:
    hero = world.get("hero")
    twit = world.get("twit")
    scenario = world.facts["scenario"]
    hero.memes["kindness"] = 1.0
    style = KINDNESS_STYLES[world.facts["params"].kindness_style]
    world.say(f"Annoyed at first, {hero.label} {style}. Then {hero.pronoun('subject')} {scenario.clue}.")
    world.say(f"The clue made the trouble look different: {twit.label} {scenario.need}.")
    world.facts["need_understood"] = True
    world.say(f"Instead of using the word 'twit' as an insult, {hero.label} spoke to the imaginary twit-bird about its choice.")
    world.say(f"This was kindness with a practical job: {hero.label} {scenario.kind_action}.")
    world.say(f'"{scenario.invitation}," {hero.pronoun("subject")} said.')


def transform_twit(world: World) -> None:
    twit = world.get("twit")
    scenario = world.facts["scenario"]
    twit.memes["shame"] = 0.0
    twit.memes["pride"] = 1.0
    twit.meters["mess"] = 0.0
    twit.location = "beside the aster"
    twit.meters["moved"] = 1.0
    world.facts["repaired"] = True
    world.say(f"The transformation was not a magic costume. It was a change of choice: {twit.label} {scenario.helpful_action}.")
    world.say(f"What had spoiled the photograph now helped make a better one.")


def act_shot(world: World) -> None:
    hero = world.get("hero")
    twit = world.get("twit")
    aster = world.get("aster")
    scenario = world.facts["scenario"]
    aster.meters["snapped"] = 1.0
    aster.meters["ready"] = 1.0
    hero.memes["joy"] = 2.0
    hero.memes["laughter"] = 1.0
    world.say(f"When the changed scene was ready, {hero.label} pressed the shutter and captured {scenario.photo}.")
    world.say(f"{hero.label} and {twit.label} laughed at the surprising picture, then checked that the {aster.label} was safe.")
    world.say(scenario.ending)
    world.say(scenario.lesson)


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    act_setup(world)
    world.para()
    act_twit_interrupts(world)
    act_kindness(world)
    transform_twit(world)
    world.para()
    act_shot(world)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    scenario = world.facts["scenario"]
    return [
        f"Write a short comedy about photography, a fictional twit-bird, and an aster in {world.setting}.",
        f"Tell how {p.hero} discovers that {p.twit} {scenario.need}, then responds with kindness.",
        f"Write a child-friendly transformation story ending with this image: {scenario.ending}",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.get("hero")
    twit = world.get("twit")
    aster = world.get("aster")
    scenario = world.facts["scenario"]
    return [
        QAItem(
            question=f"What photograph did {hero.label} hope to make in {world.setting}?",
            answer=f"{hero.label} found {aster.phrase} and {scenario.premise}.",
        ),
        QAItem(
            question=f"How did {twit.label} interfere with the photography?",
            answer=f"The fictional twit-bird {scenario.trouble}.",
        ),
        QAItem(
            question=f"What clue changed {hero.label}'s understanding of the interruption?",
            answer=f"{hero.label} {scenario.clue}. That revealed that {twit.label} {scenario.need}.",
        ),
        QAItem(
            question=f"What kind action helped solve the problem?",
            answer=f"{hero.label} {scenario.kind_action}. This gave {twit.label} a safe, useful way to help.",
        ),
        QAItem(
            question=f"How did {twit.label}'s behavior transform?",
            answer=f"The transformation was a change of choice: {twit.label} {scenario.helpful_action}.",
        ),
        QAItem(
            question="What did the final photograph show?",
            answer=f"The final photograph showed {scenario.photo}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is photography?",
            answer="Photography is the art of making pictures with a camera.",
        ),
        QAItem(
            question="What is an aster?",
            answer="An aster is a flower with petals that often looks like a little star.",
        ),
        QAItem(
            question="What does kindness do?",
            answer="Kindness can help someone feel heard and make cooperation possible. It should still name and repair any harm that occurred.",
        ),
        QAItem(
            question="What is a twit in this story world?",
            answer="Here, a twit is a made-up kind of comic bird. The word can be insulting when aimed at a person, so the story never uses it to label a person.",
        ),
        QAItem(
            question="What kind of transformation happens in this story world?",
            answer="The transformation is behavioral, not magical. The twit-bird understands the harm, accepts help, and chooses a useful action.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        bits = []
        if ent.meters:
            bits.append(f"meters={ent.meters}")
        if ent.memes:
            bits.append(f"memes={ent.memes}")
        if ent.location:
            bits.append(f"location={ent.location}")
        lines.append(f"{ent.id}: {ent.label} ({ent.type}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(setting="garden", hero="Mina", twit="Tib", aster="purple aster"),
    StoryParams(setting="park", hero="Lola", twit="Zip", aster="blue aster"),
    StoryParams(setting="backyard", hero="June", twit="Nip", aster="starry aster"),
    StoryParams(setting="greenhouse", hero="Ivy", twit="Wren", aster="aster"),
]


def resolve_valid(params: StoryParams) -> None:
    if params.hero.lower() == params.twit.lower():
        raise StoryError("The hero and the twit need different names.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("Compatible ASP story settings:")
        for (sid,) in asp_valid():
            print(f"  {sid}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            resolve_valid(p)
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            try:
                resolve_valid(params)
                sample = generate(params)
            except StoryError as e:
                print(e)
                return
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} / {p.twit} / {p.aster} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
