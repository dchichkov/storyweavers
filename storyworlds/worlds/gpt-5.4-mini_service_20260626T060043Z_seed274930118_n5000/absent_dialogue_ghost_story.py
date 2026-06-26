#!/usr/bin/env python3
"""
A small ghost-story world with dialogue, absence, and a gentle return.

Premise:
A child notices that a friendly ghost is absent from his usual place. The house
feels too quiet, and the child, a caretaker, and a lantern-holding helper search
by asking questions out loud. The ghost is shy, not lost forever; he is hiding
where the wind and moonlight feel safe. The story turns when the child listens
well enough to follow the clues, speaks kindly, and brings the ghost back into
the room.

This file is self-contained and follows the Storyweavers contract.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    present: bool = True
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    quiet: bool = True
    hiding_spots: list[str] = field(default_factory=list)


@dataclass
class Clue:
    id: str
    label: str
    kind: str
    location: str
    hint: str


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    clues: dict[str, Clue] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.clues = _copy.deepcopy(self.clues)
        clone.facts = _copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    ghost_name: str
    ghost_mood: str
    clue: str
    seed: Optional[int] = None


SETTINGS = {
    "attic": Setting(place="the attic", quiet=True, hiding_spots=["behind a trunk", "under a beam", "by a dusty window"]),
    "hall": Setting(place="the hall", quiet=True, hiding_spots=["behind the coat rack", "near a cold mirror", "under the stairs"]),
    "garden": Setting(place="the garden", quiet=True, hiding_spots=["by the hedge", "under the pear tree", "near the stone bench"]),
}

CLUES = {
    "bell": Clue(id="bell", label="small bell", kind="sound", location="a windowsill", hint="its soft ring could calm a shy ghost"),
    "lantern": Clue(id="lantern", label="paper lantern", kind="light", location="a shelf", hint="its warm glow could make the dark feel friendly"),
    "scarf": Clue(id="scarf", label="blue scarf", kind="memory", location="a chair", hint="it smelled like the house and the rain"),
}

GHOST_MOODS = ["shy", "lonely", "startled"]
HERO_NAMES = ["Mina", "June", "Theo", "Poppy", "Niko", "Elsa"]
HELPER_NAMES = ["Grandma", "Aunt May", "Papa", "Grandpa", "Mara"]
HERO_TYPES = ["girl", "boy"]
HELPER_TYPES = ["grandmother", "grandfather", "mother", "father", "aunt", "uncle"]


def _absent_rule(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("Ghost")
    hero = world.get("Hero")
    if ghost.present:
        return out
    sig = ("absent", ghost.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    out.append(f"{hero.id} noticed that {ghost.label} was absent.")
    return out


def _clue_rule(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("Hero")
    ghost = world.get("Ghost")
    clue = world.get("Clue")
    if ghost.present or hero.memes.get("worry", 0.0) < THRESHOLD:
        return out
    sig = ("clue", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    out.append(f"{hero.id} looked for a clue and found the {clue.label}.")
    return out


def _return_rule(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.get("Ghost")
    hero = world.get("Hero")
    helper = world.get("Helper")
    clue = world.get("Clue")
    if ghost.present:
        return out
    if hero.memes.get("kindness", 0.0) < THRESHOLD or hero.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    sig = ("return", ghost.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.present = True
    ghost.memes["calm"] = ghost.memes.get("calm", 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    helper.memes["relief"] = helper.memes.get("relief", 0.0) + 1
    out.append(f"The {clue.label} led them to {ghost.label}, and {ghost.label} came back in with a soft sigh.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_absent_rule, _clue_rule, _return_rule):
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(id="Hero", kind="character", type=params.hero_type, label=params.hero_name, traits=["small", "brave"]))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper_type, label=params.helper_name, traits=["gentle"]))
    ghost = world.add(Entity(id="Ghost", kind="character", type="ghost", label=params.ghost_name, traits=[params.ghost_mood], present=False))
    clue = world.add(Entity(id="Clue", kind="thing", type="clue", label=CLUES[params.clue].label, phrase=CLUES[params.clue].hint, location=CLUES[params.clue].location))
    world.clues[clue.id] = CLUES[params.clue]

    world.say(f"{hero.label} lived in {setting.place}, where even the dust seemed to whisper at night.")
    world.say(f"Every evening, {hero.label} spoke to {ghost.label}, but tonight {ghost.label} was absent from the chair by the window.")
    world.say(f"'{ghost.label}?' {hero.label} called. 'Where did you go?'")
    world.para()
    world.say(f"{helper.label} listened and said, 'If {ghost.label} is missing, we should look softly and speak kindly.'")
    world.say(f"{hero.label} held the {clue.label} and said, 'Maybe the clue knows where the quiet one is hiding.'")
    hero.memes["kindness"] = hero.memes.get("kindness", 0.0) + 1
    world.facts["clue"] = params.clue
    world.facts["ghost_mood"] = params.ghost_mood
    world.facts["setting"] = params.setting
    world.facts["hero_name"] = params.hero_name
    world.facts["helper_name"] = params.helper_name
    world.facts["ghost_name"] = params.ghost_name

    if params.clue == "bell":
        world.say("'Listen,' whispered {0}, 'the bell can answer if we call gently.'".format(helper.label))
    elif params.clue == "lantern":
        world.say("'Hold the lantern high,' said {0}, 'so the dark will not feel so big.'".format(helper.label))
    else:
        world.say(f"'{clue.label}' rested in {clue.location}, and {helper.label} said, 'It remembers this house.'")
    world.para()
    world.say(f"They followed the small sign to {setting.hiding_spots[0]}.")
    ghost.location = setting.hiding_spots[0]
    ghost.memes["shy"] = 1.0 if params.ghost_mood == "shy" else 0.5
    propagate(world, narrate=True)
    world.para()
    world.say(f"'{ghost.label},' {hero.label} said, 'you do not have to stay absent.'")
    world.say(f"{ghost.label} drifted closer, and the room felt less cold.")
    world.say(f"At the end, {ghost.label} sat by the window again, and the house was quiet in a happy way.")
    return world


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CLUES:
            combos.append((s, c))
    return combos


def explain_rejection(setting: str, clue: str) -> str:
    return f"(No story: the world cannot place the {clue} clue in {setting}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with dialogue and an absent friend.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--ghost")
    ap.add_argument("--mood", choices=GHOST_MOODS)
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    if args.setting and args.clue and (args.setting, args.clue) not in valid_combos():
        raise StoryError(explain_rejection(args.setting, args.clue))
    gender = args.gender or rng.choice(HERO_TYPES)
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice(HELPER_NAMES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    ghost_name = args.ghost or rng.choice(["Whisp", "Morrow", "Pale Jack", "Luna", "Frost"])
    mood = args.mood or rng.choice(GHOST_MOODS)
    return StoryParams(setting=setting, hero_name=hero_name, hero_type=gender, helper_name=helper_name, helper_type=helper_type, ghost_name=ghost_name, ghost_mood=mood, clue=clue)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for a young child that includes the word "absent" and has dialogue.',
        f"Tell a gentle story set in {SETTINGS[f['setting']].place} where {f['hero_name']} notices that {f['ghost_name']} is absent and asks questions out loud.",
        f"Write a spooky-but-kind story where a child and a helper follow {CLUES[f['clue']].label} clues to bring an absent ghost back.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who was absent at the beginning of the story?",
            answer=f"{f['ghost_name']} was absent, so {f['hero_name']} had to look for the ghost friend.",
        ),
        QAItem(
            question=f"What clue helped {f['hero_name']} and {f['helper_name']} search?",
            answer=f"They followed the {CLUES[f['clue']].label} because it gave them a quiet hint about where to go.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{f['ghost_name']} came back, and the house felt quiet in a happy way instead of lonely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    clue = CLUES[f["clue"]]
    return [
        QAItem(
            question="What is a lantern for?",
            answer="A lantern holds light so people can see in the dark and make a place feel less scary.",
        ),
        QAItem(
            question="Why do people speak softly in a quiet place?",
            answer="People speak softly in a quiet place so they do not startle someone who is resting or hiding nearby.",
        ),
        QAItem(
            question="What does absent mean?",
            answer="Absent means not there, like someone who should be in a place but is missing for a little while.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if not e.present:
            bits.append("present=False")
        if e.location:
            bits.append(f"location={e.location}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:6} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- place(S).
clue(C) :- clue_kind(C, _).

absent(G) :- ghost(G), not present(G).
needs_search(H, G) :- absent(G), hero(H).
found_clue(H, C) :- needs_search(H, _), clue(C).
resolved(G) :- ghost(G), present(G).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("place", sid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue_kind", cid, clue.kind))
    lines.append(asp.fact("hero"))
    lines.append(asp.fact("ghost"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show place/1."))
    return sorted(set(asp.atoms(model, "place")))


def asp_verify() -> int:
    if set(asp_valid_combos()) == set((s,) for s in SETTINGS):
        print(f"OK: clingo gate matches Python registry ({len(SETTINGS)} settings).")
        return 0
    print("MISMATCH between clingo and Python.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params)
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
    StoryParams(setting="attic", hero_name="Mina", hero_type="girl", helper_name="Grandma", helper_type="grandmother", ghost_name="Whisp", ghost_mood="shy", clue="lantern"),
    StoryParams(setting="hall", hero_name="Theo", hero_type="boy", helper_name="Papa", helper_type="father", ghost_name="Morrow", ghost_mood="lonely", clue="bell"),
    StoryParams(setting="garden", hero_name="Poppy", hero_type="girl", helper_name="Aunt May", helper_type="aunt", ghost_name="Luna", ghost_mood="startled", clue="scarf"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show place/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(valid_combos())} compatible settings/clue combos.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
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
