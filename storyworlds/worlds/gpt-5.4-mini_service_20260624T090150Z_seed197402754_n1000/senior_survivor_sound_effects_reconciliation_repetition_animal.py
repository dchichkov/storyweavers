#!/usr/bin/env python3
"""
A small animal-story world about a senior survivor, repeated sound effects, and
a gentle reconciliation.

Seed tale:
---
A senior rabbit named Bramble lived in a little meadow with a young squirrel
named Pip. Bramble had survived a hard storm long ago, so he listened closely to
every sound. Pip loved to tap sticks, clap stones, and repeat funny noises like
"tap-tap, clink-clink, hop-hop." One day, the repeated sounds startled Bramble,
and he snapped that Pip was being rude. Pip felt hurt. Then Pip noticed that
Bramble was not angry at the noise itself; he was scared because the same loud
storm sounds had once taken away his home. Pip lowered the sticks, made softer
sounds, and listened. Bramble explained his fear. Pip apologized, Bramble
apologized too, and together they made a calm game of sounds: tap, tap, hush,
hush, then a happy little laugh.

World model:
---
The domain tracks:
* typed animal entities with physical meters and emotional memes
* sound events that raise or lower fear, joy, and trust
* repeated sounds that can trigger a survivor's memory
* a reconciliation turn that only works if the apology is sincere and the
  younger animal changes the noise into a gentle game
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
# World data model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "animal"
    species: str = "animal"
    label: str = ""
    phrase: str = ""
    age_tag: str = ""
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("sound", "fear", "softness", "distance"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "trust", "hurt", "memory", "apology", "pride"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def is_senior(self) -> bool:
        return self.age_tag == "senior"


@dataclass
class Action:
    id: str
    name: str
    repeat_phrase: str
    noise_words: list[str]
    loudness: float
    helps: float
    hurts: float
    kind: str = "sound"


@dataclass
class Setting:
    place: str
    weather: str
    shelter: bool = False
    afford: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    action: str
    name1: str
    species1: str
    age1: str
    name2: str
    species2: str
    age2: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.noise_history: list[str] = []

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.noise_history = list(self.noise_history)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "meadow": Setting(place="the meadow", weather="clear", shelter=False, afford={"rustle"}),
    "barnyard": Setting(place="the barnyard", weather="breezy", shelter=True, afford={"clap"}),
    "riverbank": Setting(place="the riverbank", weather="windy", shelter=False, afford={"tap"}),
}

ACTIONS = {
    "tap": Action(
        id="tap",
        name="tap sticks",
        repeat_phrase="tap-tap, tap-tap",
        noise_words=["tap", "tap"],
        loudness=1.2,
        helps=0.2,
        hurts=0.9,
    ),
    "clap": Action(
        id="clap",
        name="clap stones",
        repeat_phrase="clap-clap, clack-clack",
        noise_words=["clap", "clack"],
        loudness=1.3,
        helps=0.1,
        hurts=1.0,
    ),
    "rustle": Action(
        id="rustle",
        name="rustle leaves",
        repeat_phrase="rustle-rustle, hush-hush",
        noise_words=["rustle", "hush"],
        loudness=0.7,
        helps=0.8,
        hurts=0.2,
    ),
}

ANIMALS = {
    "rabbit": {"article": "a", "name": "rabbit"},
    "squirrel": {"article": "a", "name": "squirrel"},
    "fox": {"article": "a", "name": "fox"},
    "hedgehog": {"article": "a", "name": "hedgehog"},
    "deer": {"article": "a", "name": "deer"},
    "owl": {"article": "an", "name": "owl"},
}

SENIOR_NAMES = ["Bramble", "Hazel", "Moss", "Willow", "Fern", "Juniper"]
SURVIVOR_NAMES = ["Pip", "Nim", "Tala", "Glim", "Otto", "Mira"]
YOUNG_NAMES = ["Pip", "Nim", "Tala", "Glim", "Otto", "Mira"]
TRAITS = ["gentle", "curious", "playful", "brave", "quiet", "bright"]


# ---------------------------------------------------------------------------
# Reasonableness gates
# ---------------------------------------------------------------------------
def valid_combo(place: str, action: str) -> bool:
    return place in SETTINGS and action in ACTIONS and action in SETTINGS[place].afford


def explain_rejection(place: str, action: str) -> str:
    if place not in SETTINGS:
        return "(No story: that place is not part of this little animal world.)"
    if action not in ACTIONS:
        return "(No story: that sound game is not part of this little animal world.)"
    return (
        f"(No story: {ACTIONS[action].name} does not fit at {SETTINGS[place].place}. "
        f"Try a sound that belongs there.)"
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def amplify_sound(world: World, speaker: Entity, action: Action) -> None:
    speaker.meters["sound"] += action.loudness
    world.noise_history.extend(action.noise_words)
    if speaker.is_senior:
        speaker.memes["memory"] += 1
        speaker.memes["fear"] += action.hurts
        speaker.memes["joy"] += action.helps * 0.2
    else:
        speaker.memes["joy"] += 0.6
        speaker.memes["pride"] += 0.2
    world.facts["last_noise"] = action.repeat_phrase


def trigger_memory(world: World, senior: Entity, action: Action) -> None:
    if senior.meters["sound"] >= THRESHOLD and len(world.noise_history) >= 2:
        sig = ("memory", senior.id, action.id)
        if sig not in world.fired:
            world.fired.add(sig)
            senior.memes["fear"] += 1.0
            senior.memes["hurt"] += 0.5
            world.say(
                f"The same {action.repeat_phrase} made {senior.id}'s ears go still."
            )


def soften_noise(world: World, junior: Entity) -> None:
    junior.meters["softness"] += 1.0
    junior.memes["trust"] += 0.7
    world.say(f"{junior.id} lowered the sticks and made the sounds small and soft.")


def reconcile(world: World, senior: Entity, junior: Entity, action: Action) -> bool:
    if senior.memes["fear"] < THRESHOLD or junior.memes["apology"] < THRESHOLD:
        return False
    if junior.meters["softness"] < THRESHOLD:
        return False
    sig = ("reconcile", senior.id, junior.id)
    if sig in world.fired:
        return True
    world.fired.add(sig)
    senior.memes["fear"] = 0.0
    senior.memes["hurt"] = max(0.0, senior.memes["hurt"] - 0.5)
    senior.memes["trust"] += 1.0
    senior.memes["joy"] += 0.8
    junior.memes["trust"] += 1.0
    junior.memes["joy"] += 0.8
    world.say(
        f"{senior.id} said the noise was not the problem; the old fear was."
    )
    world.say(
        f"{junior.id} said sorry, and {senior.id} said sorry too."
    )
    world.say(
        f"Then they made a new game: {action.repeat_phrase}, hush-hush, laugh-laugh."
    )
    return True


def tell(setting: Setting, action: Action, senior_name: str, senior_species: str, junior_name: str, junior_species: str) -> World:
    world = World(setting)
    senior = world.add(Entity(
        id=senior_name, species=senior_species, label=senior_species,
        age_tag="senior", role="survivor",
        phrase=f"senior {senior_species}", meters={"sound": 0.0, "fear": 0.0, "softness": 0.0, "distance": 0.0},
        memes={"joy": 0.2, "trust": 0.2, "hurt": 0.0, "memory": 0.5, "apology": 0.0, "pride": 0.0},
    ))
    junior = world.add(Entity(
        id=junior_name, species=junior_species, label=junior_species,
        age_tag="young", role="helper",
        phrase=f"young {junior_species}", meters={"sound": 0.0, "fear": 0.0, "softness": 0.0, "distance": 0.0},
        memes={"joy": 0.7, "trust": 0.2, "hurt": 0.0, "memory": 0.0, "apology": 0.0, "pride": 0.1},
    ))

    world.say(f"{senior.id} was a senior {senior.species} who had survived a bad storm.")
    world.say(f"{junior.id} was a young {junior.species} who loved making repeat sounds.")
    world.para()

    world.say(f"One day at {setting.place}, {junior.id} began to {action.name}.")
    world.say(f"{action.repeat_phrase} went the sticks, and the little game echoed in the air.")
    amplify_sound(world, junior, action)
    trigger_memory(world, senior, action)

    world.para()
    world.say(
        f"{senior.id} flinched and said, \"Too loud, too loud.\" "
        f"{junior.id} felt the words sting."
    )
    senior.memes["fear"] += 0.2
    junior.memes["hurt"] += 1.0
    junior.memes["trust"] = max(0.0, junior.memes["trust"] - 0.1)

    world.say(f"{junior.id} looked down, then tapped the sticks more softly.")
    soften_noise(world, junior)
    junior.memes["apology"] += 1.0
    world.say(f"\"I was only playing,\" {junior.id} said. \"I'm sorry.\"")

    if setting.shelter:
        world.say(f"They stepped under the shelter together so the air felt calmer.")

    world.para()
    if not reconcile(world, senior, junior, action):
        world.say(f"The day stayed quiet, but the two animals still watched each other carefully.")

    world.facts.update(
        senior=senior,
        junior=junior,
        action=action,
        setting=setting,
        reconciled=senior.memes["trust"] >= 1.0 and junior.memes["trust"] >= 1.0,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a: Action = f["action"]
    s: Setting = f["setting"]
    senior: Entity = f["senior"]
    junior: Entity = f["junior"]
    return [
        f'Write a gentle animal story about {senior.id}, a senior survivor, and {junior.id} making {a.repeat_phrase}.',
        f"Tell a story where {junior.id} repeats a sound, {senior.id} remembers an old fear, and they reconcile.",
        f'Write a child-friendly animal story set at {s.place} that includes "{a.repeat_phrase}" and ends in a calmer game.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    senior: Entity = f["senior"]
    junior: Entity = f["junior"]
    action: Action = f["action"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"Who is the senior survivor in the story?",
            answer=f"{senior.id} is the senior survivor. {senior.id} is a senior {senior.species} who once survived a bad storm.",
        ),
        QAItem(
            question=f"What repeated sound did {junior.id} make at {setting.place}?",
            answer=f"{junior.id} made {action.repeat_phrase}. The repeated sound was part of a playful game.",
        ),
        QAItem(
            question=f"Why did {senior.id} get upset when the sound started?",
            answer=(
                f"{senior.id} got upset because the repeated noise reminded {senior.id} of an old storm. "
                f"The sound was not dangerous by itself, but it woke up an old fear."
            ),
        ),
        QAItem(
            question=f"How did the animals fix the problem?",
            answer=(
                f"{junior.id} apologized, made the sounds softer, and listened. "
                f"Then {senior.id} explained the fear, and the two animals turned the noise into a calm game."
            ),
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=(
                f"By the end, the fear was gone and trust grew between them. "
                f"They ended together with a softer version of the same sound, now used for play instead of worry."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a survivor?",
            answer=(
                "A survivor is someone or something that got through a hard time and is still here afterward."
            ),
        ),
        QAItem(
            question="Why can repeated sounds matter to an animal?",
            answer=(
                "Repeated sounds can matter because they may feel comforting, annoying, or even remind an animal of something from before."
            ),
        ),
        QAItem(
            question="What is reconciliation?",
            answer=(
                "Reconciliation is when people or animals stop being upset, explain themselves, apologize, and become friendly again."
            ),
        ),
        QAItem(
            question="Why do soft sounds sometimes help?",
            answer=(
                "Soft sounds can help because they are gentler on the ears and can make a worried animal feel safe enough to listen."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting_valid(P) :- place(P).
action_valid(A) :- sound_action(A).

valid_story(P, A) :- setting_valid(P), action_valid(A), affords(P, A).

repeats(A) :- action(A), repeat(A, _).
survivor(S) :- animal(S), senior(S), survived_storm(S).

needs_reconciliation(S, J) :- survivor(S), young(J), hears_repeat(J, A), repeats(A).
reconciled(S, J) :- needs_reconciliation(S, J), apology(J), softens(J), apology(S).

#show valid_story/2.
#show survivor/1.
#show reconciled/2.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.shelter:
            lines.append(asp.fact("shelter", pid))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("sound_action", aid))
        lines.append(asp.fact("repeat", aid, a.repeat_phrase))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    clingo_valid = set(asp.atoms(model, "valid_story"))
    python_valid = {(p, a) for p in SETTINGS for a in ACTIONS if valid_combo(p, a)}
    if clingo_valid != python_valid:
        print("MISMATCH between ASP and Python gates:")
        if clingo_valid - python_valid:
            print(" only in ASP:", sorted(clingo_valid - python_valid))
        if python_valid - clingo_valid:
            print(" only in Python:", sorted(python_valid - clingo_valid))
        return 1
    print(f"OK: ASP and Python gates match ({len(python_valid)} valid combos).")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with senior survivor and repetition.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--action", choices=sorted(ACTIONS))
    ap.add_argument("--name1")
    ap.add_argument("--species1", choices=sorted(ANIMALS))
    ap.add_argument("--age1", choices=["senior"])
    ap.add_argument("--name2")
    ap.add_argument("--species2", choices=sorted(ANIMALS))
    ap.add_argument("--age2", choices=["young"])
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
    place = args.place or rng.choice(sorted(SETTINGS))
    action = args.action or rng.choice(sorted(SETTINGS[place].afford))
    if not valid_combo(place, action):
        raise StoryError(explain_rejection(place, action))
    senior_name = args.name1 or rng.choice(SENIOR_NAMES)
    junior_name = args.name2 or rng.choice(SURVIVOR_NAMES)
    senior_species = args.species1 or "rabbit"
    junior_species = args.species2 or "squirrel"
    return StoryParams(
        place=place,
        action=action,
        name1=senior_name,
        species1=senior_species,
        age1="senior",
        name2=junior_name,
        species2=junior_species,
        age2="young",
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIONS[params.action],
        params.name1,
        params.species1,
        params.name2,
        params.species2,
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes} role={e.role} age={e.age_tag}")
    lines.append(f"noises={world.noise_history}")
    return "\n".join(lines)


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
    StoryParams(place="meadow", action="tap", name1="Bramble", species1="rabbit", age1="senior", name2="Pip", species2="squirrel", age2="young"),
    StoryParams(place="barnyard", action="clap", name1="Hazel", species1="fox", age1="senior", name2="Mira", species2="hedgehog", age2="young"),
    StoryParams(place="riverbank", action="rustle", name1="Moss", species1="owl", age1="senior", name2="Nim", species2="deer", age2="young"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program())
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} valid stories:")
        for v in vals:
            print(" ", v)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
