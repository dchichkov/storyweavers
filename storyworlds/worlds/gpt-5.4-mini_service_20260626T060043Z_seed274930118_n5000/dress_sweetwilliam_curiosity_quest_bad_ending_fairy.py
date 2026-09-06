#!/usr/bin/env python3
"""
Fairy-tale storyworld: curiosity, a quest, and a bad ending.

A small, self-contained simulation for a cautionary fairy tale. The world is
built from a curious heroine, a delicate dress, a sweetwilliam garden, and a
quest that goes wrong when she follows her curiosity too far.

The story is state-driven:
- curiosity rises when a locked or mysterious thing appears
- a quest begins when the child decides to seek the hidden thing
- risk, damage, and loss follow from the chosen path
- the ending proves what changed

This world intentionally supports a bad ending feature: the quest may fail, and
the final image shows the cost of curiosity.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = next(
    parent for parent in Path(__file__).resolve().parents
    if (parent / "storyworlds" / "results.py").is_file()
)
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carries: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "maid"}
        male = {"boy", "prince", "king", "knight"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the rose path"
    landmark: str = "the sweetwilliam hedge"


@dataclass
class Hero:
    name: str
    gender: str
    trait: str


@dataclass
class Prize:
    label: str = "dress"
    phrase: str = "a blue dress with pearl buttons"
    type: str = "dress"
    region: str = "torso"
    plural: bool = False


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    danger: str
    promise: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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


def _curious_choice_has_cost(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    dress = world.get("dress")
    if hero.memes.get("curiosity", 0) < THRESHOLD:
        return out
    if dress.meters.get("damaged", 0) >= THRESHOLD:
        return out
    if hero.meters.get("chose_quest", 0) < THRESHOLD:
        return out
    sig = ("quest_cost", world.facts["arc_id"])
    if sig in world.fired:
        return out
    world.fired.add(sig)
    dress.meters["damaged"] = 1
    dress.meters[world.facts["damage_kind"]] = 1
    out.append(world.facts["consequence"])
    return out


def _quest_fails_after_cost(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    dress = world.get("dress")
    if dress.meters.get("damaged", 0) < THRESHOLD:
        return out
    sig = ("failed_quest", world.facts["arc_id"])
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["sorrow"] = hero.memes.get("sorrow", 0) + 1
    hero.meters["quest_failed"] = 1
    out.append(world.facts["failed_goal"])
    return out


CAUSAL_RULES = [_curious_choice_has_cost, _quest_fails_after_cost]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    name: str
    gender: str
    trait: str
    place: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class QuestArc:
    id: str
    lure: str
    goal: str
    fairy_name: str
    warning: str
    choice: str
    obstacle: str
    action: str
    consequence: str
    damage_kind: str
    truth: str
    failed_goal: str
    final_image: str
    lesson: str


SETTINGS = {
    "rose path": Setting(place="the rose path", landmark="the sweetwilliam hedge"),
    "moon garden": Setting(place="the moon garden", landmark="the sweetwilliam hedge"),
    "brook lane": Setting(place="the brook lane", landmark="the sweetwilliam hedge"),
}

GIRL_NAMES = ["Lina", "Mira", "Eira", "Nora", "Elin", "Tessa"]
BOY_NAMES = ["Ari", "Milo", "Nils", "Oren", "Perrin", "Tomas"]
HERO_NAMES = GIRL_NAMES + BOY_NAMES
TRAITS = ["curious", "gentle", "brave", "dreamy"]

QUEST_ARCS = [
    QuestArc(
        "moon_key", "a moon-pale key ticking beneath the flowers", "unlock the silver door painted on an old pear tree",
        "Pipkin", "That key belongs to the night. Wait until the moon rises.",
        "pocketed the key and tried the painted lock before sunset", "a hooked branch barred the shortest path",
        "ducked under it instead of walking around", "The hook caught the dress and tore a crescent from its hem.", "torn",
        "The silver door was only moonlight on bark, and the key became an ordinary snail shell.",
        "There was no hidden room to find, and the moon key would not tick again.",
        "On the pear-tree root lay the torn blue crescent beside one quiet shell.",
        "wonder can be enjoyed without grabbing what is not understood",
    ),
    QuestArc(
        "bell_gate", "three bell notes ringing from a gate no one else could see", "reach the fairy music before its last note",
        "Mallow", "The music crosses the bog path. Follow the stepping stones, not the sound.",
        "hurried straight toward the loudest chime", "black mud hid beneath a bright skin of duckweed",
        "jumped from a root toward a reflection that looked like stone", "The root rolled, and dark mud splashed the dress from collar to hem.", "stained",
        "The final bell came from a sleepy cow beyond the hedge, not a fairy gate.",
        "The music stopped, the imagined gate vanished, and the stains would never wash pale again.",
        "At dusk, three muddy footprints and a dull blue dress faced the silent field.",
        "an exciting sound is not a map",
    ),
    QuestArc(
        "dew_map", "a map written in beads of dew across a sweetwilliam leaf", "follow the shining route to the fairies' breakfast table",
        "Ferncap", "Read it where it grows. A dew map disappears when carried.",
        "plucked the leaf so the secret route could come along", "a warm wind curled the leaf into a tube",
        "dipped it in the brook, hoping the water would restore the lines", "The wet leaf bled green across the dress and blurred every silver stitch.", "dyed",
        "Fresh dew formed a tiny arrow pointing back to the flower that had been picked.",
        "The route was gone, and the fairies closed their breakfast before the lost map could be returned.",
        "The curled leaf floated downstream while green drops dried on the empty blue pocket.",
        "some clues must be studied gently where they belong",
    ),
    QuestArc(
        "petal_door", "a tiny red door opening and closing between the sweetwilliam stems", "ask the garden fairies for one wish",
        "Thimble", "Knock once and stand back. Never push a fairy door.",
        "knocked twice, then pulled at the door when nobody answered", "the stems twisted into a narrow living corridor",
        "squeezed sideways and tugged harder at the red handle", "The closing petals pinched the dress and pulled off every pearl button.", "buttonless",
        "Behind the door was a beetle's winter cupboard, with no wish inside.",
        "The little door sealed itself, and no fairy answered another knock that day.",
        "Six pearl buttons rested like cold seeds under the firmly closed red petals.",
        "patience matters when asking to enter another creature's home",
    ),
    QuestArc(
        "foxglove_lantern", "a violet lantern bobbing beyond the hedge at noon", "bring home a spark that could light bedtime stories",
        "Brindlewing", "A fairy light chooses its own road. Watch from the path.",
        "followed the lantern through a gap marked with crossed twigs", "the light drifted over a bed of clinging burrs",
        "crawled after it and brushed the burrs away with both sleeves", "The burrs frayed the dress until both sleeves hung in blue threads.", "frayed",
        "The lantern was a violet petal carried by a bright green beetle.",
        "The beetle flew free, but the hoped-for bedtime spark had never existed.",
        "Blue threads fluttered from the burr patch as the green beetle vanished into gold light.",
        "a beautiful moving thing need not be captured",
    ),
    QuestArc(
        "mirror_beetle", "a beetle whose back showed a castle in place of a reflection", "find the castle queen and return her missing crown",
        "Clover", "Do not chase the picture. Ask what the beetle is reflecting.",
        "ran after each new castle gleam without looking up", "the reflections led beneath a low, dripping stone arch",
        "climbed onto a mossy ledge to catch the brightest view", "Cold rusty water poured from the arch and striped the dress orange.", "rust_stained",
        "The castle stood on the far hill; its image had simply curved across the beetle's shell.",
        "By the time the truth was clear, the castle gates had closed and the crown quest was over.",
        "The beetle rested clean on a leaf while orange lines dried across the dress below.",
        "curiosity works best when it pauses to test what it sees",
    ),
    QuestArc(
        "whisper_well", "a voice in an acorn cup whispering, 'Find what the well forgot'", "recover the well's forgotten name",
        "Nettle", "Lower the cup slowly, and stop if the rope turns blue.",
        "kept lowering the cup after the rope flashed blue", "a water wheel woke and spun the rope in a sudden loop",
        "grabbed the wet rope rather than letting the cup go", "The loop snapped a jar of berry dye, soaking the dress in purple blotches.", "blotched",
        "The whisper had been the echo of wind passing through the empty acorn cup.",
        "The cup sank beyond reach, taking the supposed name and the quest with it.",
        "Purple water circled the well while one empty rope knocked softly against the stones.",
        "letting go can be wiser than forcing a mystery to continue",
    ),
    QuestArc(
        "seed_crown", "a golden seed wearing a crown of white hairs", "plant a new fairy kingdom before the seed flew away",
        "Sorrel", "A flying seed already knows where it must land. Do not tie it down.",
        "fastened the seed to a pearl button with a ribbon", "a gust pulled the ribbon toward the thorn maze",
        "held the ribbon tight and chased it between the thorns", "The ribbon tore away with the button and ripped a long seam down the dress.", "split_seam",
        "The golden seed sailed over the wall and settled by itself in a sunny field.",
        "The seed was gone, and no forced fairy kingdom grew inside the garden.",
        "Beyond the wall the seed shone freely, while a loose blue seam trailed through the thorns.",
        "help is not helpful when it ignores what a living thing needs",
    ),
    QuestArc(
        "sugar_bridge", "a trail of sparkling grains leading toward a bridge the size of a spoon", "cross into the fairies' midsummer market",
        "Honeytoe", "Those are salt crystals, not fairy sugar. Rain is coming.",
        "tasted one grain but followed the trail anyway", "the first raindrops swelled the clay beside the tiny bridge",
        "knelt to shore up the bridge with handfuls of sticky clay", "Clay hardened over the dress, making its skirt stiff and heavy.", "clay_caked",
        "The bridge belonged to ants carrying salt away from their flooded nest.",
        "The ant trail moved underground, and the imagined fairy market could no longer be reached.",
        "At sunset, ants crossed safely beneath a stiff blue skirt propped beside the empty path.",
        "careful questions reveal who truly needs help",
    ),
    QuestArc(
        "clock_moth", "a clock-faced moth beating its wings backward", "follow it to yesterday and mend a forgotten promise",
        "Tansy", "The marks are wing spots, not clock hands. Stay outside the old glasshouse.",
        "lifted the glasshouse latch when the moth slipped through", "sleeping vines tightened around the doorway",
        "pushed through before the vines could close", "The latch caught the dress and peeled away its lace collar.", "collar_lost",
        "Inside, every clock was broken, and the moth flew forward like any other moth.",
        "Yesterday never opened, so the forgotten promise remained beyond reach.",
        "A lace collar hung from the locked latch while the clock moth slept on tomorrow's window.",
        "wanting to change the past does not make every sign a doorway",
    ),
    QuestArc(
        "rainbow_spool", "a spool unwinding a rainbow thread through the flower bed", "sew the morning rainbow back before the sky faded",
        "Bluebell", "That thread is spider silk in sunlight. Do not wind it around yourself.",
        "looped the thread around the dress so it could not escape", "the hidden spider hurried home and pulled from the other end",
        "spun in circles to gather every shining strand", "The sticky silk dragged pollen and dry petals all over the dress.", "silk_stuck",
        "A cloud covered the sun, and the rainbow vanished from the ordinary web.",
        "No sky needed sewing, and the web was too tangled for its small owner to use.",
        "Under the gray cloud, a spider waited beside a blue dress wrapped in dusty petals.",
        "a quick explanation should be checked before acting on it",
    ),
    QuestArc(
        "snowberry_boat", "a white berry sailing in a walnut-shell boat along the gutter", "escort the fairy boat to the sea before twilight",
        "Dockleaf", "The gutter ends at the mill grate. Lift the boat out before then.",
        "let the boat race ahead to see whether a secret tunnel waited", "rainwater rushed faster around the bend",
        "slid down the bank and reached through the grate for the shell", "The grate snagged the dress pocket and tore it away into the stream.", "pocket_torn",
        "The walnut shell lodged safely in reeds, but the white berry was only a berry.",
        "Twilight arrived with no sea and no fairy passenger, only an unfinished quest.",
        "The empty pocket turned in the mill stream while the walnut shell rocked among quiet reeds.",
        "a promised destination should not matter more than a clear warning",
    ),
]

OPENINGS = [
    "On the morning of the sweetwilliam festival",
    "While the garden fairies hung dew on the sweetwilliam blooms",
    "Just after rain polished every sweetwilliam leaf",
    "When the sweetwilliam hedge smelled warm and spicy",
    "At the hour when fairy bells were said to wake",
    "Before the last sweetwilliam flower opened",
]

REFLECTIONS = [
    "A warning had sounded dull beside a mystery, but now its meaning was plain.",
    "The quest had begun with a question; it ended because the answer was chased too quickly.",
    "Being curious had not been wrong. Refusing to pause had caused the harm.",
    "The garden kept its secrets, and the costly choice could not be taken back.",
    "No spell repaired the result, because fairy warnings were not riddles to defeat.",
]

REQUESTS = [
    "Please tell me what it means before I choose",
    "Could I study it from the path first",
    "I only want one quick look",
    "What if the secret disappears while I wait",
    "I can be careful and still finish before supper",
    "Surely one small step cannot spoil a whole quest",
]

PAUSES = [
    "counted five heartbeats, but the lure seemed brighter after each one",
    "asked one sensible question, then rushed off before hearing the whole answer",
    "marked the safe path with three pebbles, then abandoned it at the first turn",
    "promised to stop at the warning sign, but stepped beyond it when the mystery moved",
    "looked back toward home, then let the unanswered question pull harder",
    "tested one harmless clue correctly and mistook that success for permission to continue",
]

ENDING_LEADS = [
    "Nothing frightening followed the child home, but nothing could undo the choice either.",
    "Everyone reached home safely; the loss, however, was real and lasting.",
    "The garden grew peaceful again, though the failed quest left no prize to celebrate.",
    "Supper was warm and home was safe, yet the damaged dress stayed damaged.",
    "The fairies did not punish anyone; the ordinary consequence was enough.",
    "By nightfall the danger had passed, but the hoped-for wonder was gone.",
]

ASP_RULES = r"""
curious(H) :- hero(H), curiosity(H).
near_thorn(H) :- hero(H), chooses_quest(H).
torn(D) :- dress(D), near_thorn(hero), curiosity(hero).
lost(D) :- torn(D).
bad_ending :- lost(dress).
#show curious/1.
#show near_thorn/1.
#show torn/1.
#show lost/1.
#show bad_ending/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero", "hero"),
        asp.fact("dress", "dress"),
        asp.fact("thorn", "thorn"),
        asp.fact("curiosity", "hero"),
        asp.fact("chooses_quest", "hero"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show bad_ending/0."))
    bad = any(a.name == "bad_ending" for a in model)
    if bad:
        print("OK: ASP predicts the bad ending.")
        return 0
    print("MISMATCH: ASP did not predict the bad ending.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy tale of curiosity, a quest, and a bad ending.")
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--place", choices=sorted(SETTINGS))
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
    gender = args.gender or rng.choice(["girl", "boy"])
    names = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(names)
    trait = args.trait or rng.choice(TRAITS)
    place = args.place or rng.choice(list(SETTINGS))
    return StoryParams(name=name, gender=gender, trait=trait, place=place)


def tell(params: StoryParams) -> World:
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.gender}|{params.trait}|{params.place}")
    cursor = seed
    arc = QUEST_ARCS[cursor % len(QUEST_ARCS)]
    cursor //= len(QUEST_ARCS)
    opening = OPENINGS[cursor % len(OPENINGS)]
    cursor //= len(OPENINGS)
    reflection = REFLECTIONS[cursor % len(REFLECTIONS)]
    cursor //= len(REFLECTIONS)
    request = REQUESTS[cursor % len(REQUESTS)]
    cursor //= len(REQUESTS)
    pause_action = PAUSES[cursor % len(PAUSES)]
    cursor //= len(PAUSES)
    ending_lead = ENDING_LEADS[cursor % len(ENDING_LEADS)]

    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id="hero", kind="character", type=params.gender, label=params.name, traits=[params.trait]))
    dress = world.add(Entity(id="dress", kind="thing", type="dress", label="dress", phrase="a blue dress with pearl buttons", owner=hero.id))
    hedge = world.add(Entity(id="hedge", kind="thing", type="hedge", label="sweetwilliam hedge"))
    fairy = world.add(Entity(id="fairy", kind="character", type="fairy", label=arc.fairy_name, caretaker=hedge.id))
    lure = world.add(Entity(id="lure", kind="thing", type="clue", label=arc.lure, owner=hedge.id))
    world.facts.update(
        hero=hero,
        dress=dress,
        hedge=hedge,
        fairy=fairy,
        lure=lure,
        setting=world.setting,
        arc_id=arc.id,
        goal=arc.goal,
        warning=arc.warning,
        choice=arc.choice,
        obstacle=arc.obstacle,
        action=arc.action,
        consequence=arc.consequence,
        damage_kind=arc.damage_kind,
        truth=arc.truth,
        failed_goal=arc.failed_goal,
        final_image=arc.final_image,
        lesson=arc.lesson,
        request=request,
        pause_action=pause_action,
    )

    world.say(
        f"{opening}, a {params.trait} {params.gender} named {params.name} walked through {world.setting.place}."
    )
    world.say(
        f"{params.name} wore a blue dress with pearl buttons and stopped beside the sweetwilliam hedge, where {arc.lure} waited."
    )

    world.para()
    hero.memes["curiosity"] = 1
    world.say(
        f"Curiosity filled {params.name} with questions. The discovery suggested a quest: {arc.goal}."
    )
    world.say(
        f"A thumb-high fairy named {arc.fairy_name} stepped from the flowers. \"{arc.warning}\""
    )
    world.say(f'"{request}," {params.name} replied.')

    world.para()
    world.say(f"For a moment, {params.name} {pause_action}.")
    world.say(f"Then {params.name} {arc.choice}. Soon {arc.obstacle}.")
    world.say(f"Determined to complete the quest, {params.name} {arc.action}.")
    hero.meters["chose_quest"] = 1
    world.say(
        f'"Stop now," called {arc.fairy_name}, but the warning arrived one choice too late.'
    )
    propagate(world)

    world.para()
    world.say(arc.truth)
    world.say(reflection)
    world.say(f"{ending_lead} {params.name} understood that {arc.lesson}.")
    world.say(f"It was a bad ending, though not a cruel one. {arc.final_image}")
    world.facts["bad_ending"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f"Write a fairy tale about {hero.label} and a dress, where curiosity leads to a quest to {f['goal']} and a bad ending.",
        f"Tell a short fairy story set near the sweetwilliam hedge in {f['setting'].place}, using this warning: {f['warning']}",
        f"Write a child-facing cautionary tale in which {hero.label} discovers {f['lure'].label} and learns that {f['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    qas = [
        QAItem(
            question="Who was the curious child in the fairy story?",
            answer=f"The curious child was {hero.label}, a little {hero.traits[0]} {hero.type}.",
        ),
        QAItem(
            question=f"What quest did {hero.label} choose after noticing {f['lure'].label}?",
            answer=f"{hero.label} chose a quest to {f['goal']}.",
        ),
        QAItem(
            question=f"How did {hero.label}'s choice cause the dress to be damaged?",
            answer=f"{hero.label} {f['choice']}. Then {hero.label} {f['action']}, and {f['consequence'][0].lower() + f['consequence'][1:]}",
        ),
        QAItem(
            question=f"Why was {hero.label}'s quest a bad ending even though {hero.pronoun()} returned safely?",
            answer=f"The quest failed: {f['failed_goal'][0].lower() + f['failed_goal'][1:]} The lasting final image was this: {f['final_image']}",
        ),
    ]
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sweetwilliam?",
            answer="Sweetwilliam is a garden flower with many small blossoms, often pink or red, growing in clusters.",
        ),
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity is the feeling that makes someone want to know more about something hidden or strange.",
        ),
        QAItem(
            question="What is a quest in a fairy tale?",
            answer="A quest is a journey or search for something important, often with a goal that is hard to reach.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {e.label} {' '.join(parts)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(name="Lina", gender="girl", trait="curious", place="rose path"),
    StoryParams(name="Mira", gender="girl", trait="dreamy", place="moon garden"),
    StoryParams(name="Tessa", gender="girl", trait="brave", place="brook lane"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show bad_ending/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show bad_ending/0."))
        print("bad ending:" , any(a.name == "bad_ending" for a in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 72 + "\n")


if __name__ == "__main__":
    main()
