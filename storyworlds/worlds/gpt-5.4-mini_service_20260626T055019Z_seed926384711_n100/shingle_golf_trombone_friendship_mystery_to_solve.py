#!/usr/bin/env python3
"""
storyworlds/worlds/shingle_golf_trombone_friendship_mystery_to_solve.py
=======================================================================

A small detective-style storyworld about a shingle, a golf club, and a trombone.
A child sleuth and a friend follow clues around a course, a clubhouse, and a
music room, then solve a mystery together.

The world is designed to produce a complete little story:
- beginning: a missing shingle and a curious friendship
- middle: clues are gathered, checked, and compared
- turn: the trombone sound reveals where the clue really came from
- ending: the pair fix the problem and prove what changed

This world keeps the story child-facing, concrete, and grounded in state changes.
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
# Core world model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoor: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    cause: str
    reveal: str
    location: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    kind: str
    helps: set[str]
    can_reveal: set[str]
    place: str
    plural: bool = False


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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "clubhouse": Setting(place="the clubhouse", indoor=True, affords={"investigate", "listen", "compare"}),
    "course": Setting(place="the golf course", indoor=False, affords={"investigate", "follow", "compare"}),
    "shed": Setting(place="the shed by the green", indoor=True, affords={"investigate", "search", "compare"}),
}

MYSTERIES = {
    "shingle": Mystery(
        id="shingle",
        clue="a loose roof shingle",
        cause="wind had lifted it from the clubhouse roof",
        reveal="a gust of wind had blown it down",
        location="the clubhouse roof",
        keyword="shingle",
        tags={"roof", "wind", "shingle"},
    ),
    "lost_ball": Mystery(
        id="lost_ball",
        clue="a golf ball with a fresh dent",
        cause="it bounced into the flower bed after a bad shot",
        reveal="a hard swing had sent it flying off line",
        location="the edge of the golf course",
        keyword="golf",
        tags={"golf", "ball"},
    ),
    "trombone_noise": Mystery(
        id="trombone_noise",
        clue="a trombone slide mark on the floor",
        cause="someone had practiced and bumped the stand",
        reveal="the music room had been used for a quick song practice",
        location="the music room",
        keyword="trombone",
        tags={"trombone", "music"},
    ),
}

TOOLS = {
    "magnifier": Tool(
        id="magnifier",
        label="magnifying glass",
        phrase="a small magnifying glass",
        kind="tool",
        helps={"look"},
        can_reveal={"shingle", "lost_ball", "trombone_noise"},
        place="the shed by the green",
    ),
    "notebook": Tool(
        id="notebook",
        label="notebook",
        phrase="a neat notebook",
        kind="tool",
        helps={"write"},
        can_reveal={"shingle", "lost_ball", "trombone_noise"},
        place="the clubhouse",
    ),
    "trombone": Tool(
        id="trombone",
        label="trombone",
        phrase="a shiny trombone",
        kind="instrument",
        helps={"listen"},
        can_reveal={"trombone_noise"},
        place="the music room",
    ),
}

GIRL_NAMES = ["Maya", "Lena", "Nora", "Zoe", "Ivy", "Ada"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Leo", "Milo", "Otis"]
TRAITS = ["curious", "brave", "careful", "clever", "gentle", "quick-thinking"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    detective_name: str
    detective_gender: str
    friend_name: str
    friend_gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate and story logic
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for mystery_id, mystery in MYSTERIES.items():
            if mystery.keyword in {"shingle", "golf", "trombone"}:
                combos.append((setting_id, mystery_id))
    return combos


def explain_rejection(setting_id: str, mystery_id: str) -> str:
    return f"(No story: {setting_id} does not support the mystery {mystery_id}.)"


def choose_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def make_pronouns(entity: Entity) -> tuple[str, str, str]:
    return entity.pronoun("subject"), entity.pronoun("object"), entity.pronoun("possessive")


def _has_clue(world: World, detective: Entity, mystery: Mystery) -> bool:
    return detective.memes.get(f"clue_{mystery.id}", 0.0) >= THRESHOLD


def _record_clue(world: World, detective: Entity, mystery: Mystery, label: str) -> None:
    detective.memes[f"clue_{mystery.id}"] = detective.memes.get(f"clue_{mystery.id}", 0.0) + 1
    detective.memes["confidence"] = detective.memes.get("confidence", 0.0) + 0.5
    world.facts.setdefault("clues", []).append(label)


def _look(world: World, detective: Entity, mystery: Mystery) -> None:
    if world.setting.place == "the clubhouse" and mystery.id == "shingle":
        _record_clue(world, detective, mystery, "found a loose shingle near the eaves")
        world.say(f"{detective.id} spotted a loose shingle near the wall and wrote it down.")
    elif world.setting.place == "the golf course" and mystery.id == "lost_ball":
        _record_clue(world, detective, mystery, "found a dented golf ball near the flowers")
        world.say(f"{detective.id} found a dented golf ball in the grass and frowned thoughtfully.")
    elif mystery.id == "trombone_noise":
        _record_clue(world, detective, mystery, "heard a trombone slide sound from the music room")
        world.say(f"{detective.id} heard a trombone slide squeak from the music room and looked up.")
    else:
        _record_clue(world, detective, mystery, "noticed the place was too quiet")
        world.say(f"{detective.id} looked around carefully, but the place was strangely quiet.")


def _friend_help(world: World, friend: Entity, detective: Entity, mystery: Mystery) -> None:
    friend.memes["loyalty"] = friend.memes.get("loyalty", 0.0) + 1
    detective.memes["trust"] = detective.memes.get("trust", 0.0) + 1
    world.say(f"{friend.id} stayed beside {detective.id}, ready to help with the case.")


def _compare(world: World, detective: Entity, mystery: Mystery) -> None:
    detective.memes["thinking"] = detective.memes.get("thinking", 0.0) + 1
    if mystery.id == "shingle":
        world.say("The little clue did not belong on the floor, so the pair compared it to the roof.")
    elif mystery.id == "lost_ball":
        world.say("The dent in the ball matched a bad swing, not a broken window.")
    else:
        world.say("The slide mark on the floor pointed toward music, not trouble.")


def _reveal(world: World, detective: Entity, friend: Entity, mystery: Mystery) -> None:
    detective.memes["solve"] = detective.memes.get("solve", 0.0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1
    world.facts["solved"] = True
    world.say(
        f"At last, {detective.id} solved the mystery: {mystery.reveal}. "
        f"{friend.id} grinned, because the answer fit every clue."
    )


def tell(setting: Setting, mystery: Mystery, detective_name: str, detective_gender: str,
         friend_name: str, friend_gender: str, trait: str) -> World:
    world = World(setting)
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        traits=["little", trait],
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        traits=["little", "friendly"],
    ))
    clue = world.add(Entity(
        id=mystery.id,
        kind="thing",
        type="clue",
        label=mystery.clue,
        phrase=mystery.clue,
    ))
    tool = world.add(Entity(
        id="trombone",
        kind="thing",
        type="instrument",
        label="trombone",
        phrase="a shiny trombone",
    ))
    world.facts.update(
        detective=detective,
        friend=friend,
        clue=clue,
        tool=tool,
        mystery=mystery,
        setting=setting,
    )

    # Act 1
    world.say(
        f"{detective.id} was a little {trait} detective who loved solving mysteries with {friend.id}."
    )
    world.say(
        f"One day, the pair went to {setting.place}, where something looked wrong and nobody could say why."
    )
    world.say(
        f"They found {mystery.clue}, and that made {detective.id} even more curious."
    )

    # Act 2
    world.para()
    world.say(f"{friend.id} promised to help, so the two friends began to search carefully.")
    _look(world, detective, mystery)
    _friend_help(world, friend, detective, mystery)
    _compare(world, detective, mystery)
    if mystery.id == "trombone_noise":
        world.say("Then the trombone sounded again, and the sound made the clue feel less mysterious.")
    elif mystery.id == "shingle":
        world.say("Then a breeze tapped the roof, and the shingle clue suddenly seemed easier to understand.")
    else:
        world.say("Then one more smart look showed where the ball had bounced.")

    # Act 3
    world.para()
    _reveal(world, detective, friend, mystery)
    if mystery.id == "shingle":
        world.say("They carried the shingle back and told the grown-up what the wind had done.")
    elif mystery.id == "lost_ball":
        world.say("They returned the ball and showed the player where the swing had gone wrong.")
    else:
        world.say("They set the trombone back in its stand and left the music room neat again.")
    world.say(
        f"By the end, {detective.id} and {friend.id} were smiling together, because they had solved it as a team."
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    m: Mystery = world.facts["mystery"]
    d: Entity = world.facts["detective"]
    f: Entity = world.facts["friend"]
    return [
        f'Write a short detective story for a young child about a {m.keyword}, '
        f'a clue, and two friends who solve the mystery together.',
        f"Tell a simple friendship mystery at {world.setting.place} where {d.id} and {f.id} "
        f"look for what caused the {m.keyword} clue.",
        f"Write a child-friendly detective tale that includes the words shingle, golf, and trombone.",
    ]


def story_qa(world: World) -> list[QAItem]:
    m: Mystery = world.facts["mystery"]
    d: Entity = world.facts["detective"]
    f: Entity = world.facts["friend"]
    subj_d, obj_d, pos_d = make_pronouns(d)
    subj_f, obj_f, pos_f = make_pronouns(f)

    qa = [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The story was about {d.id} and {f.id}, who worked together like a small detective team.",
        ),
        QAItem(
            question=f"What clue did {d.id} notice?",
            answer=f"{d.id} noticed {m.clue}, which made the mystery feel important right away.",
        ),
        QAItem(
            question=f"Where did the mystery happen?",
            answer=f"It happened at {world.setting.place}, where the clue was first found.",
        ),
        QAItem(
            question=f"Why did the clue seem strange?",
            answer=(
                f"It seemed strange because {m.cause}. The clue did not belong where it was found, "
                f"so {d.id} and {f.id} had to compare it with the place around it."
            ),
        ),
        QAItem(
            question=f"How did {d.id} and {f.id} feel at the end?",
            answer=(
                f"They felt happy and proud. {subj_d.capitalize()} was glad the mystery made sense, "
                f"and {subj_f} was glad they solved it together."
            ),
        ),
    ]
    if world.facts.get("solved"):
        qa.append(
            QAItem(
                question=f"What did the friends learn in the end?",
                answer=f"They learned that {m.reveal}, so the mystery had a simple answer after all.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shingle?",
            answer="A shingle is a flat piece of roof covering that helps keep rain out of a house.",
        ),
        QAItem(
            question="What is a golf course?",
            answer="A golf course is a place with grassy spaces where people play golf with clubs and balls.",
        ),
        QAItem(
            question="What is a trombone?",
            answer="A trombone is a brass instrument with a long slide that makes a loud, smooth sound.",
        ),
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, compares details, and tries to solve a mystery.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means being kind, helping each other, and having fun together.",
        ),
    ]


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting_valid(S) :- setting(S).
mystery_valid(M) :- mystery(M).

valid_story(S, M) :- setting_valid(S), mystery_valid(M),
                     supported(S, M).

solved(M) :- clue(M), reveal(M).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("clue", mid))
        lines.append(asp.fact("reveal", mid))
        lines.append(asp.fact("supported", "the_story", mid))
        for tag in sorted(m.tags):
            lines.append(asp.fact("tag", mid, tag))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", tid, h))
        for r in sorted(t.can_reveal):
            lines.append(asp.fact("can_reveal", tid, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set((s, m) for s, m in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny detective storyworld with shingle, golf, trombone, "
                    "friendship, and a mystery to solve."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--trait", choices=TRAITS)
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
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    if (setting, mystery) not in valid_combos():
        raise StoryError(explain_rejection(setting, mystery))

    gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if gender == "girl" else "girl")
    detective_name = args.name or choose_name(gender, rng)
    friend_name = args.friend or choose_name(friend_gender, rng)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        mystery=mystery,
        detective_name=detective_name,
        detective_gender=gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        MYSTERIES[params.mystery],
        params.detective_name,
        params.detective_gender,
        params.friend_name,
        params.friend_gender,
        params.trait,
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "character":
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
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
    StoryParams(
        setting="clubhouse",
        mystery="shingle",
        detective_name="Maya",
        detective_gender="girl",
        friend_name="Eli",
        friend_gender="boy",
        trait="clever",
    ),
    StoryParams(
        setting="course",
        mystery="lost_ball",
        detective_name="Noah",
        detective_gender="boy",
        friend_name="Ivy",
        friend_gender="girl",
        trait="careful",
    ),
    StoryParams(
        setting="clubhouse",
        mystery="trombone_noise",
        detective_name="Lena",
        detective_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        trait="quick-thinking",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/2."))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name}: {p.mystery} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
