#!/usr/bin/env python3
"""
Storyworld: nectarine_spree_yorkie_inner_monologue_whodunit
===========================================================

A small whodunit-style story world with inner monologue, centered on a missing
nectarine during a little yorkie's spree.

Premise:
- A child notices a clue trail of nectarine juice and crumbs.
- The yorkie is the only one small enough to reach the scene.
- The detective's inner monologue drives the search.
- The story resolves when the true culprit is identified and the nectarines are
  recovered or accounted for.

This file follows the Storyweavers storyworld contract.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "woman"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "man"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kitchen"
    mood: str = "quiet"
    affordances: set[str] = field(default_factory=set)


@dataclass
class Clue:
    name: str
    phrase: str
    reveal: str
    mess: str
    kind: str
    location: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SuspectProfile:
    id: str
    label: str
    alibi: str
    motive: str
    clue_fit: str
    innocent_if: str


@dataclass
class StoryParams:
    setting: str
    clue: str
    suspect: str
    detective_name: str
    detective_type: str
    sidekick: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def qmonologue(thought: str) -> str:
    return f"(Inside {thought})"


def setting_line(setting: Setting) -> str:
    return {
        "the kitchen": "The kitchen was quiet, with a pale window and a table that held the morning still.",
        "the pantry": "The pantry smelled like wood, spice, and a secret that had not yet been named.",
        "the garden": "The garden looked tidy at first, but little tracks in the dirt hinted otherwise.",
        "the hallway": "The hallway was narrow and bright, a place where every tiny sound could matter.",
    }[setting.place]


def clue_sentence(clue: Clue) -> str:
    return {
        "nectarine": "A sticky orange shine had been left behind on the counter, and a single nectarine pit sat like a witness.",
        "crumbs": "Crumbs were scattered in a careful little line, as if someone had walked and nibbled at the same time.",
        "pawprints": "Tiny pawprints marked the floor, neat and quick, too small for any grown-up shoes.",
        "napkin": "A folded napkin had been dragged aside, as if it had been used in a hurry.",
    }[clue.name]


def suspect_profiles() -> dict[str, SuspectProfile]:
    return {
        "yorkie": SuspectProfile(
            id="yorkie",
            label="the yorkie",
            alibi="had been dozing by the sunlit rug",
            motive="loved sweet snacks and fast dashes",
            clue_fit="small pawprints and a sugar smear fit a tiny dog",
            innocent_if="the bark collar was still dry and the napkin had been moved later",
        ),
        "cat": SuspectProfile(
            id="cat",
            label="the cat",
            alibi="had been perched on the windowsill the whole time",
            motive="liked high shelves and watching people panic",
            clue_fit="could leave pawprints, but not the low nibble marks",
            innocent_if="the cat never touched the counter and stayed clean",
        ),
        "brother": SuspectProfile(
            id="brother",
            label="the older brother",
            alibi="was still outside kicking a ball",
            motive="might have wanted the last nectarine",
            clue_fit="had the size for the kitchen, but not the tiny pawprints",
            innocent_if="his shoes were muddy, not sticky",
        ),
    }


SETTING_REGISTRY = {
    "kitchen": Setting(place="the kitchen", mood="quiet", affordances={"search", "snack"}),
    "pantry": Setting(place="the pantry", mood="hushed", affordances={"search", "snack"}),
    "garden": Setting(place="the garden", mood="bright", affordances={"search", "chase"}),
    "hallway": Setting(place="the hallway", mood="still", affordances={"search"}),
}

CLUE_REGISTRY = {
    "nectarine": Clue(
        name="nectarine",
        phrase="a ripe nectarine",
        reveal="a sticky orange gleam",
        mess="sticky",
        kind="fruit",
        location="counter",
        tags={"fruit", "sweet", "orange"},
    ),
    "crumbs": Clue(
        name="crumbs",
        phrase="crumbs from a snack",
        reveal="a trail of crumbs",
        mess="crumbly",
        kind="food",
        location="floor",
        tags={"food", "trail"},
    ),
    "pawprints": Clue(
        name="pawprints",
        phrase="tiny pawprints",
        reveal="small pawprints",
        mess="dusty",
        kind="tracks",
        location="floor",
        tags={"animal", "tracks"},
    ),
    "napkin": Clue(
        name="napkin",
        phrase="a dropped napkin",
        reveal="a crumpled napkin",
        mess="paper",
        kind="cloth",
        location="table",
        tags={"cloth", "hasty"},
    ),
}

SIDEKICKS = ["yorkie", "cat", "brother"]
DETECTIVE_NAMES = ["Mina", "Ivy", "Theo", "Nina", "Milo", "June"]
DETECTIVE_TYPES = ["girl", "boy"]


ASP_RULES = r"""
% A clue is relevant when it can appear in the selected setting.
relevant(S, C) :- setting(S), clue(C), located_in(C, S).

% A suspect is plausible when their profile fits the observed clue set.
plausible(U) :- suspect(U), clue_fit(U, C), observed(C).

% The yorkie is guilty when the small-paw clue and nectarines are both present.
guilty(yorkie) :- suspect(yorkie), observed(pawprints), observed(nectarine).

% A whodunit is valid when there is exactly one guilty suspect and a reasonable
% explanation reaches the ending.
valid_story(S, C, U) :- relevant(S, C), plausible(U), guilty(U).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTING_REGISTRY.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affordances):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CLUE_REGISTRY.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("located_in", cid, params_for_clue_location(c)))
        for t in sorted(c.tags):
            lines.append(asp.fact("tag", cid, t))
    for sid in SIDEKICKS:
        lines.append(asp.fact("suspect", sid))
    return "\n".join(lines)


def params_for_clue_location(clue: Clue) -> str:
    if clue.name == "pawprints":
        return "garden"
    if clue.name == "crumbs":
        return "hallway"
    return "kitchen"


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set(valid_story_triples())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} triples).")
        return 0
    print("MISMATCH between clingo and Python:")
    print(" only in clingo:", sorted(clingo_set - python_set))
    print(" only in python:", sorted(python_set - clingo_set))
    return 1


def valid_story_triples() -> list[tuple]:
    triples = []
    for s in SETTING_REGISTRY:
        for c in CLUE_REGISTRY:
            for u in SIDEKICKS:
                if reasonableness_gate(s, c, u):
                    triples.append((s, c, u))
    return triples


def reasonableness_gate(setting: str, clue: str, suspect: str) -> bool:
    if setting not in SETTING_REGISTRY or clue not in CLUE_REGISTRY or suspect not in SIDEKICKS:
        return False
    if setting == "garden" and clue == "pawprints" and suspect == "yorkie":
        return True
    if clue == "nectarine" and suspect == "yorkie":
        return True
    if clue == "crumbs" and suspect in {"yorkie", "brother"}:
        return True
    if clue == "napkin" and suspect in {"cat", "brother"}:
        return True
    return False


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with a nectarine, a spree, and a yorkie.")
    ap.add_argument("--setting", choices=SETTING_REGISTRY)
    ap.add_argument("--clue", choices=CLUE_REGISTRY)
    ap.add_argument("--suspect", choices=SIDEKICKS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=DETECTIVE_TYPES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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
    setting = args.setting or rng.choice(list(SETTING_REGISTRY))
    clue = args.clue or rng.choice(list(CLUE_REGISTRY))
    suspect = args.suspect or rng.choice(SIDEKICKS)
    if not reasonableness_gate(setting, clue, suspect):
        raise StoryError("No valid whodunit fits those choices; try the yorkie with nectarines or pawprints.")
    name = args.name or rng.choice(DETECTIVE_NAMES)
    gender = args.gender or rng.choice(DETECTIVE_TYPES)
    sidekick = args.sidekick or ("yorkie" if suspect != "yorkie" else "cat")
    if sidekick == suspect:
        sidekick = "cat" if suspect != "cat" else "brother"
    return StoryParams(setting=setting, clue=clue, suspect=suspect, detective_name=name, detective_type=gender, sidekick=sidekick)


def generate_world(params: StoryParams) -> World:
    setting = SETTING_REGISTRY[params.setting]
    clue = CLUE_REGISTRY[params.clue]
    profiles = suspect_profiles()
    world = World(setting)
    detective = world.add(Entity(id=params.detective_name, kind="character", type=params.detective_type, label="detective"))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="dog" if params.sidekick == "yorkie" else "cat", label=params.sidekick))
    suspect = world.add(Entity(id=params.suspect, kind="character", type="dog" if params.suspect == "yorkie" else "boy", label=profiles[params.suspect].label))
    world.facts.update(detective=detective, sidekick=sidekick, suspect=suspect, clue=clue, profile=profiles[params.suspect])
    return world


def narrate(world: World, params: StoryParams) -> None:
    clue = world.facts["clue"]
    profile: SuspectProfile = world.facts["profile"]
    detective: Entity = world.facts["detective"]
    sidekick: Entity = world.facts["sidekick"]
    suspect: Entity = world.facts["suspect"]

    world.say(f"{detective.id} was the sort of detective who noticed when silence felt too tidy to be true.")
    world.say(f"{detective.pronoun().capitalize()} kept a sharp inner monologue, because in a whodunit, the loudest thing was often the thought nobody said out loud.")
    world.say(setting_line(world.setting))
    world.say(f"A {clue.phrase} should have been there, but it was gone, and that was the first strange thing.")
    world.say(qmonologue("If the nectarine vanished during a spree, then the trail must still be speaking somewhere."))

    world.para()
    world.say(clue_sentence(clue))
    if clue.name == "nectarine":
        world.say("The sticky shine pointed toward the counter edge, then down toward the floor, as if the missing fruit had been carried in a hurry.")
    elif clue.name == "crumbs":
        world.say("The crumbs made a little path that did not look accidental, and that made the detective think twice.")
    elif clue.name == "pawprints":
        world.say("The pawprints were too tiny for the grown-ups, and that made the yorkie look suddenly very important.")
    else:
        world.say("The napkin looked innocent, but a detective knew better than to trust anything folded in a rush.")

    world.para()
    world.say(qmonologue(f"{profile.alibi.capitalize()}, but alibis were only useful if they could survive a second look."))
    world.say(f"{suspect.label.capitalize()} had {profile.motive}, which sounded suspicious until it sounded exactly like the clue.")
    world.say(f"{sidekick.id.capitalize()} tilted {sidekick.pronoun('possessive')} head as if the room had asked a question only it could hear.")
    if params.suspect == "yorkie":
        world.say("The little yorkie had once darted through the kitchen on a gleeful spree, and that memory now fit the evidence a little too well.")
        world.say(qmonologue("Small paws, a sweet smell, and a missing nectarine. That was not nothing."))
    else:
        world.say(qmonologue("The yorkie was near, but the clue did not yet say the yorkie was guilty. A true detective waits for the last piece."))
        world.say("The detective followed the trail anyway, because a good case never minded a cautious pair of shoes.")

    world.para()
    if params.suspect == "yorkie":
        world.say("At last, the detective knelt and noticed a shiny smear on the yorkie's whiskers.")
        world.say("The yorkie had not meant to be clever; it had simply been greedy, quick, and far too small to hide the truth.")
        world.say(f'"The nectarine was yours all along," {detective.id} said softly, and the yorkie gave a guilty little sneeze.')
        world.say("Behind a bowl and a fallen napkin, the last bright slice of fruit turned up at last, safe and only slightly bruised.")
    else:
        world.say(f"The detective looked again and saw that {suspect.label} was only nearby, not responsible.")
        world.say("The yorkie, meanwhile, sat with the calm face of someone who had already been forgiven for a smaller sin.")
        world.say("The real answer was hidden by the obvious clue, and once the detective noticed that, the case opened like a locked drawer with the right key.")
        world.say("The nectarine was found tucked in a napkin-lined bowl, where a hurried hand had placed it and then forgotten it.")

    world.para()
    world.say(qmonologue("So that was it: the spree, the clue, the false alarm, and the tiny culprit or the tiny witness. Either way, the room made sense again."))
    world.say(f"{detective.id} set the fruit on the table, and the room felt less like a mystery and more like breakfast.")
    world.say(f"{sidekick.id} wagged or purred its way into peace, and the final image was simple: one nectarine, no longer missing, and one detective who trusted the clues.")

    world.facts["resolved"] = True
    world.facts["guilty"] = params.suspect == "yorkie"


def generation_prompts(world: World) -> list[str]:
    params = world.facts
    clue: Clue = params["clue"]
    suspect: SuspectProfile = params["profile"]
    return [
        f"Write a child-friendly whodunit about a missing nectarine and a tiny spree in {world.setting.place}.",
        f"Tell a mystery story where a detective follows {clue.reveal} and suspects {suspect.label}.",
        f"Write a short story with inner monologue clues, a yorkie, and a lost nectarine.",
    ]


def story_qa(world: World) -> list[QAItem]:
    detective: Entity = world.facts["detective"]
    clue: Clue = world.facts["clue"]
    suspect: SuspectProfile = world.facts["profile"]
    sidekick: Entity = world.facts["sidekick"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {detective.id}, a careful detective who used quiet thoughts to solve a small mystery.",
        ),
        QAItem(
            question=f"What clue first made the case feel strange?",
            answer=f"The first clue was {clue.reveal}, which showed that something had happened in a hurry.",
        ),
        QAItem(
            question=f"Why did {detective.id} pay attention to {suspect.label}?",
            answer=f"{suspect.label.capitalize()} had {suspect.motive}, and the clue fit that story a little too neatly.",
        ),
        QAItem(
            question=f"What was special about the detective's thinking?",
            answer="The detective kept an inner monologue, so the reader could hear the careful thoughts that helped connect the clues.",
        ),
        QAItem(
            question=f"What happened to the nectarine by the end?",
            answer="The missing nectarine was found again and put back where it belonged, so the room felt tidy and solved.",
        ),
    ]
    if world.facts.get("guilty"):
        qa.append(QAItem(
            question=f"Why did the yorkie seem guilty?",
            answer="Because the tiny pawprints, the sticky shine, and the eager little spree all pointed toward the yorkie.",
        ))
    else:
        qa.append(QAItem(
            question=f"Was the yorkie the real culprit?",
            answer="No. The yorkie was part of the mystery, but the final clue showed that the missing nectarine had been moved by mistake, not stolen by the yorkie.",
        ))
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a nectarine?",
            answer="A nectarine is a smooth-skinned fruit, a little like a peach but without fuzzy skin.",
        ),
        QAItem(
            question="What is a spree?",
            answer="A spree is a burst of quick activity, when someone or something dashes around doing a lot in a short time.",
        ),
        QAItem(
            question="What is a yorkie?",
            answer="A yorkie is a tiny dog, short for Yorkshire terrier, and it has quick little feet.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet stream of thoughts a character has inside their head.",
        ),
        QAItem(
            question="What makes a whodunit a whodunit?",
            answer="A whodunit is a mystery story where the reader follows clues to find out who caused the problem.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.extend(world.trace)
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    narrate(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTING_REGISTRY:
        for c in CLUE_REGISTRY:
            for u in SIDEKICKS:
                if reasonableness_gate(s, c, u):
                    out.append((s, c, u))
    return out


CURATED = [
    StoryParams(setting="kitchen", clue="nectarine", suspect="yorkie", detective_name="Mina", detective_type="girl", sidekick="cat"),
    StoryParams(setting="pantry", clue="crumbs", suspect="brother", detective_name="Theo", detective_type="boy", sidekick="yorkie"),
    StoryParams(setting="garden", clue="pawprints", suspect="yorkie", detective_name="Ivy", detective_type="girl", sidekick="cat"),
    StoryParams(setting="hallway", clue="napkin", suspect="cat", detective_name="June", detective_type="girl", sidekick="yorkie"),
]


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid()
        print(f"{len(triples)} valid triples")
        for t in triples:
            print(t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name}: {p.setting} / {p.clue} / {p.suspect}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
