#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/kook_hearth_dissension_aquarium_quest_inner_monologue.py
================================================================================================

A standalone storyworld for a heartwarming aquarium tale with a quest, inner
monologue, and a little humor. The world is built around a child, a kooky helper,
and a small disagreement that resolves into a caring ending.

The story uses these seed words naturally:
- kook
- hearth
- dissension

Setting: aquarium
Style: heartwarming
Features: quest, inner monologue, humor
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class AquariumZone:
    id: str
    name: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    clue: str
    goal: str
    prize: str
    humor: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    name: str
    label: str
    oddity: str
    warmth: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Conflict:
    id: str
    subject: str
    object: str
    reason: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, zone: AquariumZone) -> None:
        self.zone = zone
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        if not ent.meters:
            ent.meters = {}
        if not ent.memes:
            ent.memes = {}
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
        import copy
        w = World(self.zone)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w


def _rule_dissension(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.memes.get("dissension", 0.0) >= THRESHOLD and ("dissension", "fired") not in world.fired:
        world.fired.add(("dissension", "fired"))
        child.memes["worry"] = child.memes.get("worry", 0.0) + 1
        out.append("The child's worry got louder than the humming tanks.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in (_rule_dissension,):
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


ZONES = {
    "main_hall": AquariumZone(
        id="main_hall",
        name="the aquarium's main hall",
        mood="bright and echoing",
        affords={"quest", "talk", "listen"},
    ),
    "hearth_room": AquariumZone(
        id="hearth_room",
        name="the warm hearth room",
        mood="quiet and cozy",
        affords={"quest", "talk", "listen", "rest"},
    ),
}

QUESTS = {
    "shell_map": Quest(
        id="shell_map",
        clue="a shell-shaped map pointing to the coral garden",
        goal="find the missing star charm for the classroom display",
        prize="the star charm",
        humor="It was the sort of map that looked like it had been drawn by a crab with excellent manners.",
        tags={"quest", "humor", "star"},
    ),
    "lantern_note": Quest(
        id="lantern_note",
        clue="a note tucked under a lantern near the jellyfish tank",
        goal="return the little otter key to the hearth shelf",
        prize="the little otter key",
        humor="The note was so crooked it seemed to be doing a tiny dance.",
        tags={"quest", "humor", "otter"},
    ),
    "fish_key": Quest(
        id="fish_key",
        clue="a fish-shaped tag beside the tide pool",
        goal="bring the bright pebble to the hearth nook",
        prize="the bright pebble",
        humor="The tag looked proud enough to swim away if nobody was watching.",
        tags={"quest", "humor", "pebble"},
    ),
}

HELPERS = {
    "kook_keeper": Helper(
        id="kook_keeper",
        name="Milo",
        label="the kooky keeper",
        oddity="wore socks with tiny whales on them and spoke to the signpost like it was an old friend",
        warmth="smiled as if every lost thing deserved a gentle search",
        tags={"kook", "warmth"},
    ),
    "kook_artist": Helper(
        id="kook_artist",
        name="Nia",
        label="the kooky artist",
        oddity="carried crayons in a teapot and tied all her pencils with a ribbon",
        warmth="laughed softly and made everyone feel welcome",
        tags={"kook", "warmth"},
    ),
}

CONFLICTS = {
    "shortcut": Conflict(
        id="shortcut",
        subject="the child",
        object="the route",
        reason="the child wanted to rush past the tanks, but the guardian wanted to slow down and listen",
        tags={"dissension"},
    ),
    "quiet_rule": Conflict(
        id="quiet_rule",
        subject="the child",
        object="the joke",
        reason="the child wanted to giggle too loudly, and the guardian reminded them the fish liked peace",
        tags={"dissension", "humor"},
    ),
}

GIRL_NAMES = ["Maya", "Luna", "Nora", "Ava", "Iris", "Ellie"]
BOY_NAMES = ["Owen", "Leo", "Theo", "Finn", "Noah", "Eli"]


@dataclass
class StoryParams:
    zone: str
    quest: str
    helper: str
    conflict: str
    child_name: str
    child_gender: str
    guardian: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(zone="main_hall", quest="shell_map", helper="kook_keeper", conflict="shortcut",
                child_name="Maya", child_gender="girl", guardian="mother"),
    StoryParams(zone="hearth_room", quest="lantern_note", helper="kook_artist", conflict="quiet_rule",
                child_name="Owen", child_gender="boy", guardian="father"),
    StoryParams(zone="hearth_room", quest="fish_key", helper="kook_keeper", conflict="shortcut",
                child_name="Nora", child_gender="girl", guardian="mother"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for z in ZONES:
        for q in QUESTS:
            for h in HELPERS:
                if "quest" in ZONES[z].affords and "kook" in HELPERS[h].tags:
                    combos.append((z, q, h))
    return combos


def _build_world(params: StoryParams) -> World:
    if params.zone not in ZONES:
        raise StoryError("Unknown aquarium zone.")
    if params.quest not in QUESTS:
        raise StoryError("Unknown quest.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    if params.conflict not in CONFLICTS:
        raise StoryError("Unknown conflict.")
    zone = ZONES[params.zone]
    quest = QUESTS[params.quest]
    helper = HELPERS[params.helper]
    conflict = CONFLICTS[params.conflict]

    world = World(zone)
    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.child_gender,
        label=params.child_name,
        meters={"steps": 0.0},
        memes={"joy": 0.0, "dissension": 0.0, "curiosity": 1.0, "warmth": 0.0},
        attrs={"guardian": params.guardian},
    ))
    guardian = world.add(Entity(
        id="guardian",
        kind="character",
        type=params.guardian,
        label=f"the {params.guardian}",
        meters={},
        memes={"care": 1.0},
        attrs={},
    ))
    guide = world.add(Entity(
        id="guide",
        kind="character",
        type="adult",
        label=helper.label,
        meters={},
        memes={"warmth": 1.0},
        attrs={"name": helper.name, "oddity": helper.oddity},
    ))
    world.facts.update(child=child, guardian=guardian, guide=guide, quest=quest,
                       helper=helper, conflict=conflict, zone=zone, params=params)
    return world


def tell(world: World) -> None:
    f = world.facts
    child: Entity = f["child"]
    guardian: Entity = f["guardian"]
    guide: Entity = f["guide"]
    quest: Quest = f["quest"]
    helper: Helper = f["helper"]
    conflict: Conflict = f["conflict"]

    child.memes["joy"] += 1
    world.say(
        f"{child.label} and {guardian.label_word if hasattr(guardian, 'label_word') else guardian.label} arrived at {world.zone.name}, where the air felt {world.zone.mood}."
    )
    world.say(
        f"They met {helper.label}, who {helper.oddity} and {helper.warmth}. "
        f"{quest.humor}"
    )
    world.say(
        f"{child.label} came on a small quest: {quest.clue}, because {quest.goal} mattered to the whole family."
    )
    world.para()

    child.memes["dissension"] += 1
    world.say(
        f'At first there was a little dissension. {conflict.reason}.'
    )
    world.say(
        f'{child.label} looked at the tanks and thought, "I can be brave without being loud. '
        f'Also, fish do not need my opera voice."'
    )
    propagate(world, narrate=True)

    world.para()
    child.meters["steps"] += 1
    child.memes["joy"] += 1
    child.memes["warmth"] += 1
    if world.zone.id == "hearth_room":
        world.say(
            f"Together they followed the clue to the hearth nook, where the room was soft with lamplight and calm voices."
        )
    else:
        world.say(
            f"Together they followed the clue past the blue tanks and the rippling lights, until the trail led them to the right display."
        )
    world.say(
        f"{guide.label} found {quest.prize} tucked exactly where the clue promised."
    )
    world.say(
        f'{guardian.label} smiled. "{child.label}, you solved it."'
    )
    world.say(
        f'{child.label} grinned and thought, "A quest is easier when the helper is a kook and the family stays kind."'
    )
    world.say(
        f"In the end, {quest.prize} went home to the hearth shelf, {guardian.label} laughed, and {child.label} walked out of the aquarium feeling proud, cozy, and loved."
    )

    world.facts["resolved"] = True


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming aquarium story for a young child that includes the words "kook", "hearth", and "dissension".',
        f"Tell a gentle quest story set in an aquarium where {f['child'].label} works with a kooky helper and ends up at a hearth nook.",
        f"Write a humorous but caring story about a small disagreement at the aquarium that turns into a successful quest and a warm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    guardian: Entity = f["guardian"]
    quest: Quest = f["quest"]
    helper: Helper = f["helper"]
    conflict: Conflict = f["conflict"]
    zone: AquariumZone = f["zone"]
    return [
        QAItem(
            question=f"What kind of place did {child.label} visit?",
            answer=f"{child.label} visited an aquarium. It was a place full of water, quiet animals, and bright, moving light.",
        ),
        QAItem(
            question=f"Who helped with the quest?",
            answer=f"{helper.label} helped with the quest. {helper.warmth} and made the search feel safe and cheerful.",
        ),
        QAItem(
            question=f"Why was there dissension at first?",
            answer=f"There was dissension because {conflict.reason}. The child and guardian did not agree for a moment, but they stayed kind.",
        ),
        QAItem(
            question=f"How did the quest end?",
            answer=f"The quest ended well when they found {quest.prize} and brought it back to the hearth shelf. The child left feeling proud, cozy, and loved.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an aquarium?",
            answer="An aquarium is a place where people go to see fish and other water animals in tanks and exhibits.",
        ),
        QAItem(
            question="What does a hearth mean in a story?",
            answer="A hearth is a warm, cozy place or fire area in a home. In stories, the word can also suggest comfort and togetherness.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a search or mission to find something important. It often means following clues step by step.",
        ),
        QAItem(
            question="What does dissension mean?",
            answer="Dissension means a disagreement or a small conflict. People can still be kind while they work through it.",
        ),
        QAItem(
            question="What is a kook?",
            answer="A kook is someone who is a little odd or very quirky, usually in a funny or harmless way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(sample.prompts)
    parts.append("")
    parts.append("== story qa ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes} attrs={e.attrs}")
    lines.append(f"facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    tell(world)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming aquarium quest storyworld.")
    ap.add_argument("--zone", choices=ZONES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.zone is None or c[0] == args.zone)
              and (args.quest is None or c[1] == args.quest)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid aquarium story matches the given options.)")
    zone, quest, helper = rng.choice(sorted(combos))
    conflict = args.conflict or rng.choice(sorted(CONFLICTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guardian = args.guardian or rng.choice(["mother", "father"])
    return StoryParams(zone=zone, quest=quest, helper=helper, conflict=conflict,
                       child_name=name, child_gender=gender, guardian=guardian)


def valid_storyworld_params() -> list[StoryParams]:
    return CURATED


ASP_RULES = r"""
valid(Z,Q,H) :- zone(Z), quest(Q), helper(H), quest_capable(Z), kooky(H).
quest_capable(main_hall).
quest_capable(hearth_room).
kooky(kook_keeper).
kooky(kook_artist).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for z in ZONES:
        lines.append(asp.fact("zone", z))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH: ASP and Python valid-combos differ.")
        print("python-only:", sorted(py - cl))
        print("asp-only:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    if ok:
        print(f"OK: ASP/Python parity and generate() smoke test passed ({len(py)} combos).")
        return 0
    return 1


def explain_rejection() -> str:
    return "(No story: that combination does not fit the aquarium quest world.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            sample = generate(params)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
