#!/usr/bin/env python3
"""
Story world: a folk tale about a leopard, a missing gem, and a swishy clue.

A small, self-contained classical simulation in the Storyweavers style.
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

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    place: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("wear", 0.0)
        self.meters.setdefault("loss", 0.0)
        self.memes.setdefault("curiosity", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("joy", 0.0)
        self.memes.setdefault("humor", 0.0)


@dataclass
class Setting:
    name: str
    place: str
    weather: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Quest:
    problem: str
    clue_kind: str
    clue_place: str
    ending_place: str
    helper: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []
        self.fired: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        chunk: list[str] = []
        for line in self.lines:
            if line == "":
                if chunk:
                    out.append(" ".join(chunk))
                    chunk = []
            else:
                chunk.append(line)
        if chunk:
            out.append(" ".join(chunk))
        return "\n\n".join(out)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "moonlit_wood": Setting(
        name="moonlit wood",
        place="the moonlit wood",
        weather="soft night",
        affordances={"search", "listen", "run"},
    ),
    "river_bend": Setting(
        name="river bend",
        place="the river bend",
        weather="bright day",
        affordances={"search", "listen", "splash"},
    ),
    "hill_village": Setting(
        name="hill village",
        place="the hill village",
        weather="windy day",
        affordances={"search", "ask", "gather"},
    ),
}

PROTAGONISTS = {
    "leopard": {
        "type": "leopard",
        "label": "leopard",
        "phrase": "a clever leopard with bright eyes",
        "traits": ["clever", "quick", "kind"],
    }
}

GEMS = {
    "amber_gem": {
        "label": "amber gem",
        "phrase": "a small amber gem",
        "glow": "golden",
        "owner_title": "keeper",
    },
    "moon_gem": {
        "label": "moon gem",
        "phrase": "a pale moon gem",
        "glow": "silvery",
        "owner_title": "elder",
    },
    "river_gem": {
        "label": "river gem",
        "phrase": "a blue river gem",
        "glow": "blue",
        "owner_title": "fisher",
    },
}

CLUES = {
    "swish": {
        "label": "swish",
        "phrase": "a swish in the brush",
        "place": "the thorny brush",
        "effect": "made the leaves whisper and bend",
    },
    "spark": {
        "label": "spark",
        "phrase": "a tiny spark on the ground",
        "place": "the mossy stones",
        "effect": "blinked like a firefly",
    },
    "footprint": {
        "label": "footprint",
        "phrase": "a soft footprint in the mud",
        "place": "the muddy bank",
        "effect": "pointed the way",
    },
}

HELPERS = {
    "owl": {
        "label": "owl",
        "phrase": "a sleepy owl",
        "style": "wise",
    },
    "hare": {
        "label": "hare",
        "phrase": "a quick hare",
        "style": "funny",
    },
    "mouse": {
        "label": "mouse",
        "phrase": "a tiny mouse",
        "style": "helpful",
    },
}

QUESTS = {
    "find_gem": Quest(
        problem="the gem had gone missing",
        clue_kind="swish",
        clue_place="the thorny brush",
        ending_place="the old hollow tree",
        helper="owl",
    ),
    "solve_noise": Quest(
        problem="the night made a strange little noise",
        clue_kind="swish",
        clue_place="the reed bed",
        ending_place="the river stones",
        helper="hare",
    ),
    "find_path": Quest(
        problem="the path back home was lost",
        clue_kind="footprint",
        clue_place="the muddy bank",
        ending_place="the lantern gate",
        helper="mouse",
    ),
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A quest is valid if the chosen setting supports searching and the clue exists there.
valid_story(S, G, C, H) :- setting(S), gem(G), clue(C), helper(H),
                           affords(S, search), clue_found_in(C, S).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("affords", sid, a))
    for gid in GEMS:
        lines.append(asp.fact("gem", gid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_found_in", cid, clue_place_to_setting(c["place"])))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def clue_place_to_setting(place: str) -> str:
    if place == "the thorny brush":
        return "moonlit_wood"
    if place == "the reed bed":
        return "river_bend"
    return "hill_village"


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set((s, g, c, h) for (s, g, c, h) in asp_valid_stories())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for sid, setting in SETTINGS.items():
        if "search" not in setting.affordances:
            continue
        for gid in GEMS:
            for cid, clue in CLUES.items():
                if clue_place_to_setting(clue["place"]) != sid:
                    continue
                for hid in HELPERS:
                    combos.append((sid, gid, cid, hid))
    return combos


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    gem: str
    clue: str
    helper: str
    name: str = "Nia"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="leopard",
        label="leopard",
        phrase=PROTAGONISTS["leopard"]["phrase"],
        traits=list(PROTAGONISTS["leopard"]["traits"]),
    ))
    gem_def = GEMS[params.gem]
    clue_def = CLUES[params.clue]
    helper_def = HELPERS[params.helper]

    gem = world.add(Entity(
        id="gem",
        kind="thing",
        type="gem",
        label=gem_def["label"],
        phrase=gem_def["phrase"],
        owner=hero.id,
        place=world.setting.place,
    ))
    clue = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label=clue_def["label"],
        phrase=clue_def["phrase"],
        place=clue_def["place"],
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=params.helper,
        label=helper_def["label"],
        phrase=helper_def["phrase"],
        traits=[helper_def["style"]],
    ))

    world.facts.update(
        hero=hero,
        gem=gem,
        clue=clue,
        helper=helper,
        setting=world.setting,
        quest=QUESTS[params.clue if params.clue in QUESTS else "find_gem"],
        params=params,
    )
    return world


def introduce(world: World) -> None:
    hero: Entity = world.facts["hero"]
    gem: Entity = world.facts["gem"]
    setting: Setting = world.setting
    world.say(
        f"Once in {setting.place}, there lived {hero.phrase}."
    )
    world.say(
        f"One bright morning, {hero.id} treasured {gem.phrase}, and it shone in {gem_def_glow(gem.id, world)} light."
    )
    world.say(
        f"{hero.id} loved a good riddle and often smiled at small troubles, for even a mystery can wear a funny face."
    )


def gem_def_glow(gem_id: str, world: World) -> str:
    for gid, g in GEMS.items():
        if g["label"] == world.get(gem_id).label:
            return g["glow"]
    return "soft"


def start_quest(world: World) -> None:
    hero: Entity = world.facts["hero"]
    gem: Entity = world.facts["gem"]
    clue: Entity = world.facts["clue"]
    helper: Entity = world.facts["helper"]
    setting: Setting = world.setting
    quest: Quest = world.facts["quest"]

    world.para()
    world.say(
        f"Then a problem came: {quest.problem}."
    )
    hero.memes["worry"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} said, \"I must solve this mystery and find what was lost.\""
    )
    world.say(
        f"So {hero.id} began a quest through {setting.place}, listening for {clue.phrase}."
    )
    if world.facts["params"].clue == "swish":
        world.say(
            f"The swish was sly and funny, as if the bushes were trying not to giggle."
        )
    else:
        world.say(
            f"The clue seemed small, but {hero.id} knew small things can point to big truths."
        )
    world.say(
        f"At last, {hero.id} met {helper.phrase}, who offered help with a grin."
    )


def solve_mystery(world: World) -> None:
    hero: Entity = world.facts["hero"]
    gem: Entity = world.facts["gem"]
    clue: Entity = world.facts["clue"]
    helper: Entity = world.facts["helper"]
    params: StoryParams = world.facts["params"]
    quest: Quest = world.facts["quest"]

    world.para()
    world.say(
        f"{helper.id} pointed at {clue.phrase} and said, \"Follow it to the old hollow tree.\""
    )
    world.say(
        f"{hero.id} followed the clue carefully, and the trail led exactly where the helper promised."
    )
    world.say(
        f"There, tucked in a knot of roots, was the missing {gem.label}."
    )
    if params.clue == "swish":
        world.say(
            f"The swish turned out to be a rabbit with a leaf on its tail, and even the rabbit looked embarrassed."
        )
        hero.memes["humor"] += 1
    elif params.clue == "footprint":
        world.say(
            f"The footprint belonged to a tiny mouse carrying a crumb, which made the whole mystery feel less scary."
        )
        hero.memes["humor"] += 1
    else:
        world.say(
            f"The little spark came from a beetle on a pebble, and that made the answer sparkle even brighter."
        )
        hero.memes["humor"] += 1
    gem.place = quest.ending_place
    hero.meters["wear"] += 1
    hero.memes["joy"] += 1


def ending(world: World) -> None:
    hero: Entity = world.facts["hero"]
    gem: Entity = world.facts["gem"]
    helper: Entity = world.facts["helper"]

    world.para()
    world.say(
        f"{hero.id} carried the {gem.label} home and laughed at the silly little trail that had fooled everyone."
    )
    world.say(
        f"{helper.id} laughed too, and the moonlit wood felt warm with a solved mystery and a happy heart."
    )
    world.say(
        f"That night, the gem lay safe again, and {hero.id} slept with a smile, ready for the next quest."
    )


# ---------------------------------------------------------------------------
# Parameters / sampling
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A folk-tale story world about a leopard, a gem, and a humorous mystery."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--gem", choices=GEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.gem:
        combos = [c for c in combos if c[1] == args.gem]
    if args.clue:
        combos = [c for c in combos if c[2] == args.clue]
    if args.helper:
        combos = [c for c in combos if c[3] == args.helper]
    if not combos:
        raise StoryError("(No valid story matches the given options.)")
    setting, gem, clue, helper = rng.choice(sorted(combos))
    name = args.name or rng.choice(["Nia", "Lea", "Tari", "Malo", "Suri"])
    return StoryParams(setting=setting, gem=gem, clue=clue, helper=helper, name=name)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    introduce(world)
    start_quest(world)
    solve_mystery(world)
    ending(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]
    return [
        f"Write a folk tale about a leopard named {params.name} who must solve a mystery about a lost {GEMS[params.gem]['label']}.",
        f"Tell a gentle quest story with a funny swish clue and a brave leopard at {world.setting.place}.",
        f"Create a short story for young children where a leopard follows a clue, finds a gem, and laughs at the answer.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]
    hero: Entity = world.facts["hero"]
    gem: Entity = world.facts["gem"]
    helper: Entity = world.facts["helper"]
    clue: Entity = world.facts["clue"]
    quest: Quest = world.facts["quest"]

    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a clever leopard who goes on a quest to solve a mystery.",
        ),
        QAItem(
            question=f"What was missing in the story?",
            answer=f"The missing thing was {gem.phrase}, and finding it was the mystery to solve.",
        ),
        QAItem(
            question=f"Who helped {hero.id} with the search?",
            answer=f"{helper.id} helped by pointing toward {clue.phrase} and showing the way to the answer.",
        ),
        QAItem(
            question=f"Why did {hero.id} begin the quest?",
            answer=f"{hero.id} began the quest because {quest.problem}.",
        ),
        QAItem(
            question=f"What made the story a little funny?",
            answer=f"The swish clue turned out to be a silly little trick of the woods, so the mystery ended with a laugh.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to look for something important or to solve a problem.",
        ),
        QAItem(
            question="What is a gem?",
            answer="A gem is a shiny stone that can sparkle like a tiny treasure.",
        ),
        QAItem(
            question="What does swish mean?",
            answer="Swish is the soft sound of something moving through grass, leaves, or water.",
        ),
        QAItem(
            question="Why do folk tales often repeat clues and helpers?",
            answer="Folk tales often use repeating clues and helpful friends so the story feels easy to follow and fun to remember.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== Generation prompts ==")
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Trace / emit / main
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(
            f"{e.id}: type={e.type} kind={e.kind} place={e.place!r} meters={e.meters} memes={e.memes}"
        )
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="moonlit_wood", gem="amber_gem", clue="swish", helper="owl", name="Nia"),
    StoryParams(setting="river_bend", gem="river_gem", clue="footprint", helper="mouse", name="Tari"),
    StoryParams(setting="hill_village", gem="moon_gem", clue="spark", helper="hare", name="Suri"),
]


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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for row in stories:
            print("  ", row)
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = ""
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
