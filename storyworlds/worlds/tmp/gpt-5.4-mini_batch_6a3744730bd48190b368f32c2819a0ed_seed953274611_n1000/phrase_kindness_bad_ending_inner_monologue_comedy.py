#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/phrase_kindness_bad_ending_inner_monologue_comedy.py
=====================================================================================

A small comedy storyworld about a child trying to be kind with a phrase that
lands in an unexpectedly bad ending. The story is driven by simulated state:
characters carry physical meters and emotional memes, a tiny object can be
passed around, and the narration follows the turn from hope to mishap.

Premise:
- A child wants to say something kind.
- An inner monologue rehearses the phrase.
- The phrase is used at the wrong moment.
- Kindness is real, but the outcome is a comic bad ending: embarrassment,
  misunderstanding, and a small mess.

The world is intentionally tiny and child-facing. The prose should feel like a
complete story with setup, turn, and ending image.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
INNER_MONOLOGUE_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Scene:
    place: str
    setup: str
    trouble_spot: str
    ending_image: str


@dataclass
class PhrasePack:
    id: str
    phrase: str
    kind: str
    literal: str
    misfire: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mishap:
    id: str
    trigger: str
    impact: str
    fail: str
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    scene: str
    phrase: str
    mishap: str
    comfort: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent_kind: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_embarrass(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["blurted"] < THRESHOLD:
        return out
    sig = ("embarrass",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["embarrassment"] += 1
    world.get("helper").memes["surprise"] += 1
    out.append("__embarrass__")
    return out


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.meters["blurted"] < THRESHOLD:
        return out
    if child.meters["mess"] >= THRESHOLD:
        return out
    sig = ("mess",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["mess"] += 1
    world.get("room").meters["mess"] += 1
    out.append("__mess__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("embarrass", "social", _r_embarrass),
    Rule("mess", "physical", _r_mess),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mishap(world: World, child: Entity, phrase: PhrasePack, mishap: Mishap) -> dict:
    sim = world.copy()
    _say_phrase(sim, sim.get("child"), phrase, narrate=False)
    return {
        "embarrassed": sim.get("child").memes["embarrassment"] >= THRESHOLD,
        "mess": sim.get("room").meters["mess"] >= THRESHOLD,
    }


def _say_phrase(world: World, child: Entity, phrase: PhrasePack, narrate: bool = True) -> None:
    child.meters["blurted"] += 1
    child.memes["hope"] += 1
    propagate(world, narrate=narrate)


def build_world() -> None:
    pass


def setup(world: World, scene: Scene, child: Entity, helper: Entity, parent: Entity) -> None:
    child.memes["kindness"] += 1
    child.memes["anxiety"] += 1
    helper.memes["curiosity"] += 1
    world.say(
        f"At {scene.place}, {child.id} and {helper.id} were trying to be helpful. "
        f"{scene.setup}"
    )
    world.say(
        f"{child.id} kept glancing at the problem spot, {scene.trouble_spot}, and trying to think of the nicest thing to say."
    )


def inner_monologue(world: World, child: Entity, phrase: PhrasePack, comfort: Comfort) -> None:
    child.memes["inner_monologue"] += 1
    world.say(
        f'In {child.id}\'s head, a brave little voice rehearsed: "{phrase.phrase}." '
        f'It sounded perfect there, especially with {comfort.phrase} tucked under {child.pronoun("possessive")} arm.'
    )


def warn_world(world: World, helper: Entity, parent: Entity, mishap: Mishap) -> None:
    helper.memes["worry"] += 1
    world.say(
        f"{helper.id} looked at the situation and made a face. "
        f'"That might turn into a {mishap.trigger}," {helper.id} whispered, because {parent.label_word} was already busy.'
    )


def blurt(world: World, child: Entity, phrase: PhrasePack) -> None:
    child.memes["courage"] += 1
    if phrase.kind == "kind":
        world.say(
            f'{child.id} took a tiny breath and said, "{phrase.phrase}"'
        )
    else:
        world.say(f'{child.id} said, "{phrase.phrase}"')


def bad_ending(world: World, child: Entity, helper: Entity, parent: Entity, mishap: Mishap) -> None:
    child.memes["embarrassment"] += 1
    helper.memes["surprise"] += 1
    world.say(
        f"Unfortunately, the phrase landed at exactly the wrong time, so {mishap.fail}. "
        f"The whole room went quiet for one awkward beat."
    )
    world.say(
        f"Then {parent.id} turned around, saw the tiny {mishap.impact}, and raised an eyebrow so high it nearly touched the ceiling."
    )


def comic_finish(world: World, child: Entity, helper: Entity, comfort: Comfort, parent: Entity) -> None:
    world.say(
        f"{child.id} wished {child.pronoun('possessive')} feet could hide under the floorboards. "
        f"{helper.id} tried not to laugh, but {helper.pronoun()} snorted once anyway."
    )
    world.say(
        f"{parent.label_word.capitalize()} sighed, wiped up the {comfort.label}, and said, "
        f'"Kindness is lovely. Next time, maybe deliver the phrase after the juice box has stopped flying."'
    )
    world.say(
        f"By the end, {child.id} was red-faced, the table was sticky, and the phrase was still kind -- just not timed very well."
    )


SCENES = {
    "classroom": Scene(
        place="the classroom",
        setup="The paper stars were shining on the wall, and the snack table had a very serious juice box on it.",
        trouble_spot="the snack table",
        ending_image="a sticky table with a lopsided paper star"
    ),
    "birthday": Scene(
        place="the birthday party",
        setup="The balloons bobbed like sleepy clouds, and the cake looked proud of itself.",
        trouble_spot="the cake table",
        ending_image="a cake with one frosting fingerprint and a heroic napkin"
    ),
    "kitchen": Scene(
        place="the kitchen",
        setup="The cookies were cooling, and everybody was trying to act like they would not steal one early.",
        trouble_spot="the counter",
        ending_image="a crumb trail beside a careful stack of plates"
    ),
}

PHRASES = {
    "phrase": PhrasePack(
        id="phrase",
        phrase="You are doing a really good job",
        kind="kind",
        literal="phrase",
        misfire="a kind phrase at the wrong moment",
        tags={"phrase", "kindness"},
    ),
    "praise": PhrasePack(
        id="praise",
        phrase="That was very brave of you",
        kind="kind",
        literal="phrase",
        misfire="a praise phrase with bad timing",
        tags={"phrase", "kindness"},
    ),
    "apology": PhrasePack(
        id="apology",
        phrase="I'm sorry about the mess",
        kind="kind",
        literal="phrase",
        misfire="an apology phrase spoken too soon",
        tags={"phrase", "kindness"},
    ),
}

MISHAPS = {
    "juice": Mishap(
        id="juice",
        trigger="juice splash",
        impact="juice spill",
        fail="the juice box wobbled, spun, and whooshed a stripe of juice across the floor",
        power=2,
        tags={"juice", "spill"},
    ),
    "cake": Mishap(
        id="cake",
        trigger="cake wobble",
        impact="frosting smudge",
        fail="the cake plate tilted, and a snowy smear of frosting slid right onto the tablecloth",
        power=2,
        tags={"cake", "spill"},
    ),
    "crumbs": Mishap(
        id="crumbs",
        trigger="crumb avalanche",
        impact="crumb drift",
        fail="a sneeze from the cookie tray sent crumbs skittering everywhere like tiny comedians",
        power=1,
        tags={"crumbs", "spill"},
    ),
}

COMFORTS = {
    "napkin": Comfort(id="napkin", label="napkin", phrase="a heroic napkin", tags={"napkin"}),
    "towel": Comfort(id="towel", label="towel", phrase="a folded towel", tags={"towel"}),
    "spoon": Comfort(id="spoon", label="spoon", phrase="a shiny spoon", tags={"spoon"}),
}

GIRL_NAMES = ["Maya", "Lena", "Zoe", "Nina", "Ella", "Ruby", "Ivy", "Tara"]
BOY_NAMES = ["Finn", "Noah", "Owen", "Theo", "Jasper", "Milo", "Ben", "Eli"]
HELPER_NAMES = ["Pip", "Sami", "June", "Ari", "Kit", "Mina"]
TRAITS = ["careful", "polite", "funny", "thoughtful", "cheerful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene in SCENES:
        for phrase in PHRASES:
            for mishap in MISHAPS:
                if scene == "classroom" and mishap == "crumbs":
                    combos.append((scene, phrase, mishap))
                elif scene == "birthday" and mishap in {"cake", "juice"}:
                    combos.append((scene, phrase, mishap))
                elif scene == "kitchen" and mishap in {"juice", "crumbs"}:
                    combos.append((scene, phrase, mishap))
    return combos


@dataclass
class StoryParams:
    scene: str
    phrase: str
    mishap: str
    comfort: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    parent_kind: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "kindness": [("What is kindness?",
                  "Kindness means choosing words or actions that help someone feel safe, noticed, or cared for.")],
    "phrase": [("What is a phrase?",
                "A phrase is a small group of words that says one idea, like a little sentence piece.")],
    "embarrassment": [("What is embarrassment?",
                      "Embarrassment is the squirmy feeling you get when something awkward happens and everybody notices.")],
    "juice": [("Why can juice be messy?",
               "Juice can be messy because it is liquid and it spreads quickly when it spills.")],
    "cake": [("Why is cake frosting slippery?",
              "Frosting is soft and smooth, so it can smear and slide if the plate tips.")],
    "crumbs": [("Why do crumbs scatter?",
                "Crumbs are tiny and light, so they bounce and skitter easily when something shakes.")],
}
KNOWLEDGE_ORDER = ["kindness", "phrase", "embarrassment", "juice", "cake", "crumbs"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a comedy story for a young child that includes the word "{PHRASES[f["phrase"]].literal}" and a kind thought that goes hilariously wrong.',
        f"Tell a short story where {f['child'].id} practices a kind phrase in an inner monologue, then blurts it at the worst possible moment.",
        f"Write a gentle-but-silly story about kindness, an awkward bad ending, and a phrase that everyone remembers afterward.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, parent = f["child"], f["helper"], f["parent"]
    phrase = f["phrase"]
    scene = f["scene"]
    mishap = f["mishap"]
    qa = [
        QAItem(
            question="What was the child trying to do?",
            answer=(
                f"{child.id} was trying to be kind and say the phrase out loud at the right time. "
                f"{child.id} kept practicing it in {child.pronoun('possessive')} head first so it would sound gentle."
            ),
        ),
        QAItem(
            question="Why did the ending go badly?",
            answer=(
                f"It went badly because {child.id} said {phrase.phrase} right when the room was already one tiny step from a mishap. "
                f"That timing made the {mishap.trigger} turn into an awkward mess instead of a smooth, helpful moment."
            ),
        ),
        QAItem(
            question="What did the helper do?",
            answer=(
                f"{helper.id} noticed the trouble first and tried to keep the situation calm. "
                f"{helper.id} could not stop the awkward moment completely, but {helper.id} helped everyone stay safe and less flustered."
            ),
        ),
        QAItem(
            question="How did the story end?",
            answer=(
                f"It ended with {child.id} blushing, the {scene.place} feeling silly and sticky, and {parent.label_word} cleaning up. "
                f"The phrase was kind, but the day turned into a comic bad ending."
            ),
        ),
    ]
    if f.get("turned"):
        qa.append(
            QAItem(
                question=f"What happened when {child.id} said the phrase?",
                answer=(
                    f"The phrase came out in a burst, and the little setup tipped into a mishap right away. "
                    f"{mishap.fail.capitalize()}"
                ),
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["phrase"].tags) | set(world.facts["mishap"].tags)
    out: list[QAItem] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            q, a = KNOWLEDGE[key][0]
            out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def tell(scene: Scene, phrase: PhrasePack, mishap: Mishap, comfort: Comfort,
         child_name: str, child_gender: str, helper_name: str, helper_gender: str,
         parent_kind: str) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    parent = world.add(Entity(id="parent", kind="character", type=parent_kind, label="the parent", role="parent"))
    room = world.add(Entity(id="room", type="room", label=scene.place))

    child.id = child_name
    helper.id = helper_name

    world.entities.pop("child")
    world.entities.pop("helper")
    world.entities[child_name] = child
    world.entities[helper_name] = helper
    world.entities["child"] = child
    world.entities["helper"] = helper
    world.entities["parent"] = parent
    world.entities["room"] = room

    setup(world, scene, child, helper, parent)
    world.para()
    inner_monologue(world, child, phrase, comfort)
    warn_world(world, helper, parent, mishap)
    blurt(world, child, phrase)
    _say_phrase(world, child, phrase)
    world.para()
    bad_ending(world, child, helper, parent, mishap)
    comic_finish(world, child, helper, comfort, parent)

    world.facts.update(
        scene=scene,
        phrase=phrase,
        mishap=mishap,
        comfort=comfort,
        child=child,
        helper=helper,
        parent=parent,
        turned=True,
    )
    return world


def setup(world: World, scene: Scene, child: Entity, helper: Entity, parent: Entity) -> None:
    child.memes["kindness"] += 1
    helper.memes["support"] += 1
    world.say(
        f"{scene.place.capitalize()} was busy and bright. {scene.setup}"
    )
    world.say(
        f"{child.id} and {helper.id} were trying to be nice without getting in anyone's way."
    )


def inner_monologue(world: World, child: Entity, phrase: PhrasePack, comfort: Comfort) -> None:
    child.memes["inner_monologue"] += 1
    world.say(
        f"In {child.id}'s head, a tiny narrator kept whispering the same {phrase.literal}: "
        f'"{phrase.phrase}." {child.id} rehearsed it while clutching {comfort.phrase} like a lucky charm.'
    )


def warn_world(world: World, helper: Entity, parent: Entity, mishap: Mishap) -> None:
    helper.memes["worry"] += 1
    world.say(
        f"{helper.id} noticed the room wobbling toward {mishap.trigger} and gave {parent.label_word} a quick look that meant, 'Maybe keep an eye on this.'"
    )


def blurt(world: World, child: Entity, phrase: PhrasePack) -> None:
    world.say(
        f'{child.id} smiled, took a breath, and said, "{phrase.phrase}"'
    )


def _say_phrase(world: World, child: Entity, phrase: PhrasePack, narrate: bool = True) -> None:
    child.meters["blurted"] += 1
    child.memes["hope"] += 1
    propagate(world, narrate=narrate)


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError("Unknown scene.")
    if params.phrase not in PHRASES:
        raise StoryError("Unknown phrase pack.")
    if params.mishap not in MISHAPS:
        raise StoryError("Unknown mishap.")
    if params.comfort not in COMFORTS:
        raise StoryError("Unknown comfort object.")

    world = tell(
        SCENES[params.scene],
        PHRASES[params.phrase],
        MISHAPS[params.mishap],
        COMFORTS[params.comfort],
        params.child_name,
        params.child_gender,
        params.helper_name,
        params.helper_gender,
        params.parent_kind,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection() -> str:
    return "(No story: this tiny world only tells phrases that can tip into a comic bad ending.)"


def valid_combo(params: StoryParams) -> bool:
    return params.scene in SCENES and params.phrase in PHRASES and params.mishap in MISHAPS and params.comfort in COMFORTS


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for pid, p in PHRASES.items():
        lines.append(asp.fact("phrase", pid))
        lines.append(asp.fact("kind", pid, p.kind))
    for mid in MISHAPS:
        lines.append(asp.fact("mishap", mid))
    for cid in COMFORTS:
        lines.append(asp.fact("comfort", cid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,M) :- scene(S), phrase(P), mishap(M).
turns_bad(P,M) :- phrase(P), mishap(M).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = {(s, p, m) for s, p, m in valid_combos()}
    cl = set(asp_valid_combos())
    if cl == py:
        print(f"OK: gate matches valid_combos() ({len(cl)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    try:
        sample = generate(CURATED[0])
        print(f"OK: smoke-tested generate() with story length {len(sample.story)}.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about kindness, a phrase, and a bad ending.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--phrase", choices=PHRASES)
    ap.add_argument("--mishap", choices=MISHAPS)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent-kind", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene and args.scene not in SCENES:
        raise StoryError("Unknown scene.")
    if args.phrase and args.phrase not in PHRASES:
        raise StoryError("Unknown phrase.")
    if args.mishap and args.mishap not in MISHAPS:
        raise StoryError("Unknown mishap.")

    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.phrase is None or c[1] == args.phrase)
              and (args.mishap is None or c[2] == args.mishap)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene, phrase, mishap = rng.choice(sorted(combos))
    comfort = args.comfort or rng.choice(sorted(COMFORTS))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    if helper_name == child_name:
        helper_name = (helper_name + "_2")
    parent_kind = args.parent_kind or rng.choice(["mother", "father"])
    return StoryParams(
        scene=scene,
        phrase=phrase,
        mishap=mishap,
        comfort=comfort,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        parent_kind=parent_kind,
    )


CURATED = [
    StoryParams(scene="classroom", phrase="phrase", mishap="crumbs", comfort="napkin", child_name="Maya", child_gender="girl", helper_name="Pip", helper_gender="boy", parent_kind="mother"),
    StoryParams(scene="birthday", phrase="praise", mishap="cake", comfort="towel", child_name="Finn", child_gender="boy", helper_name="June", helper_gender="girl", parent_kind="father"),
    StoryParams(scene="kitchen", phrase="apology", mishap="juice", comfort="spoon", child_name="Lena", child_gender="girl", helper_name="Ari", helper_gender="boy", parent_kind="mother"),
]


def generate_sample(params: StoryParams) -> StorySample:
    return generate(params)


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
        print(asp_program(show="#show valid/3.\n#show turns_bad/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program(show="#show valid/3."))
        combos = asp.atoms(model, "valid")
        print(f"{len(combos)} valid combos:")
        for t in combos:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate_sample(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate_sample(params)
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
            header = f"### {p.child_name}: {p.phrase} in {p.scene} ({p.mishap})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
