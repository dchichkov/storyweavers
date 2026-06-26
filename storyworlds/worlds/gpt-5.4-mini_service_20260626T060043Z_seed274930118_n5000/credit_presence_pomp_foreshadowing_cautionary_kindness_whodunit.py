#!/usr/bin/env python3
"""
A small whodunit storyworld: a child notices clues at a pomp-filled ceremony,
learns a cautionary lesson about not blaming too fast, and ends by giving credit
to the kind helper who quietly protected everyone.

The generated stories are built from a simulated world model with meters and
memes:
- physical meters: dampness, dust, missing, shine, order
- emotional memes: curiosity, caution, blame, kindness, pomp, relief, credit

The core premise is a tiny mystery in a community hall. Something important goes
missing during a grand, slightly pompous event. Foreshadowing clues appear early,
the child detective follows them, and kindness resolves the riddle.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    present: bool = True

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "lady"}
        male = {"boy", "father", "dad", "man", "gentleman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing_item: str
    clue_item: str
    cause: str
    suspect_hint: str
    at_risk_reason: str
    resolution: str
    tag: str


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    sidekick: str
    adult: str
    seed: Optional[int] = None


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


SETTINGS = {
    "community_hall": Setting(
        place="the community hall",
        detail="A bright banner hung over the stage, and chairs waited in straight rows.",
        affords={"ceremony"},
    ),
    "library": Setting(
        place="the library",
        detail="Tall shelves made soft walls, and the reading table sat under a rainy window.",
        affords={"ceremony"},
    ),
    "garden_room": Setting(
        place="the garden room",
        detail="Potted plants stood near the windows, and little flags swayed from the ceiling.",
        affords={"ceremony"},
    ),
}

MYSTERIES = {
    "trophy": Mystery(
        id="trophy",
        missing_item="the silver trophy",
        clue_item="a damp cloth",
        cause="a leak above the display shelf",
        suspect_hint="the wet cloth and the moved stool were not signs of theft at all",
        at_risk_reason="the trophy could tarnish if water dripped on it",
        resolution="the helper moved the trophy to a dry shelf and left a note",
        tag="trophy",
    ),
    "crown": Mystery(
        id="crown",
        missing_item="the paper crown",
        clue_item="a ribbon scrap",
        cause="the wind from an open door",
        suspect_hint="the ribbon scrap matched the stage decorations",
        at_risk_reason="the crown could crumple if it blew onto the wet floor",
        resolution="the helper tucked the crown into a safe box and tied the door shut",
        tag="crown",
    ),
    "banner": Mystery(
        id="banner",
        missing_item="the blue banner",
        clue_item="a bit of twine",
        cause="the banner pole slipped loose",
        suspect_hint="the twine matched the knot on the spare pole",
        at_risk_reason="the banner could tear if it dragged on the floor",
        resolution="the helper rolled the banner carefully and placed it beside the stage",
        tag="banner",
    ),
}

NAMES = ["Maya", "Nina", "Owen", "Theo", "Iris", "Luna", "Ben", "June", "Piper", "Eli"]
SIDEKICKS = ["friend", "cousin", "brother", "sister"]
ADULTS = ["librarian", "janitor", "caretaker", "stage helper"]


@dataclass
class StoryState:
    hero: Entity
    sidekick: Entity
    adult: Entity
    item: Entity
    clue: Entity
    setting: Setting
    mystery: Mystery


def build_world(params: StoryParams) -> StoryState:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    hero = Entity(id=params.name, kind="character", type=params.gender, meters={"curiosity": 0.0}, memes={"curiosity": 0.0, "caution": 0.0, "credit": 0.0, "relief": 0.0})
    sidekick = Entity(id=params.sidekick, kind="character", type="child", meters={"curiosity": 0.0}, memes={"curiosity": 0.0, "caution": 0.0})
    adult = Entity(id=params.adult, kind="character", type="adult", meters={"busy": 0.0}, memes={"kindness": 0.0, "pomp": 0.0, "credit": 0.0})
    item = Entity(id=mystery.id, kind="thing", type="thing", label=mystery.missing_item, present=False, meters={"missing": 1.0, "shine": 1.0}, memes={"importance": 1.0})
    clue = Entity(id="clue", kind="thing", type="thing", label=mystery.clue_item, present=True, meters={"damp": 1.0, "dust": 0.0}, memes={"foreshadowing": 1.0})

    world = StoryState(hero=hero, sidekick=sidekick, adult=adult, item=item, clue=clue, setting=setting, mystery=mystery)
    return world


def introduce(world: World, st: StoryState) -> None:
    h = st.hero
    s = st.sidekick
    a = st.adult
    h.memes["curiosity"] += 1
    a.memes["pomp"] += 1
    world.say(
        f"{h.id} was a careful little {h.type} who loved noticing tiny things. "
        f"On the day of the grand ceremony at {world.setting.place}, {s.id} stayed close, and {a.id} arrived with a lot of pomp."
    )
    world.say(world.setting.detail)
    world.say(
        f"A shiny space was waiting for {st.mystery.missing_item}, and everyone said it was the most important thing in the room."
    )


def foreshadow(world: World, st: StoryState) -> None:
    h = st.hero
    clue = st.clue
    h.memes["curiosity"] += 1
    h.memes["caution"] += 1
    world.say(
        f"Before anyone noticed the trouble, {h.id} saw {clue.label} near the table."
    )
    world.say(
        f"It looked small, but it was a clue, and {h.id} remembered that little things can point to a bigger answer."
    )
    world.say(
        f"{st.mystery.at_risk_reason.capitalize()}, so {h.id} did not touch anything yet."
    )


def cautionary_turn(world: World, st: StoryState) -> None:
    h = st.hero
    s = st.sidekick
    h.memes["caution"] += 1
    s.memes["curiosity"] += 1
    world.say(
        f"{s.id} whispered that maybe someone had taken {st.mystery.missing_item}, but {h.id} shook {h.pronoun('possessive')} head."
    )
    world.say(
        f'"Let us not blame anyone yet," {h.id} said. "A clue can be kinder than a guess."'
    )
    world.say(
        f"Then {h.id} noticed wet marks on the floor, which made the mystery feel less like a theft and more like a careful rescue."
    )


def investigate(world: World, st: StoryState) -> None:
    h = st.hero
    a = st.adult
    h.memes["curiosity"] += 1
    a.memes["kindness"] += 1
    world.say(
        f"{h.id} followed the damp marks to the side shelf, where a small note was folded under a book."
    )
    world.say(
        f"The note did not accuse anyone. It only said, 'I moved {st.mystery.missing_item} because of the leak.'"
    )
    world.say(
        f"That was when the room's puzzle started to make sense: {st.mystery.cause} had put the display at risk."
    )


def reveal(world: World, st: StoryState) -> None:
    h = st.hero
    a = st.adult
    item = st.item
    item.present = True
    item.meters["missing"] = 0.0
    item.meters["shine"] = 1.0
    a.memes["credit"] += 1
    h.memes["credit"] += 1
    h.memes["relief"] += 1
    world.say(
        f"At last, {h.id} found {st.mystery.missing_item} safely tucked away, just where a kind helper had left it."
    )
    world.say(
        f"The helper had not hidden it for fun; {st.mystery.resolution}."
    )
    world.say(
        f"{h.id} gave {a.id} full credit, and the whole room felt lighter."
    )
    world.say(
        f"By the end, the pomp had faded, the clue had been explained, and the mystery had turned into a thank-you."
    )


def tell_story(params: StoryParams) -> World:
    st = build_world(params)
    world = World(st.setting)
    world.facts.update(setting=st.setting, mystery=st.mystery)

    introduce(world, st)
    world.para()
    foreshadow(world, st)
    cautionary_turn(world, st)
    world.para()
    investigate(world, st)
    reveal(world, st)

    world.facts.update(
        hero=st.hero,
        sidekick=st.sidekick,
        adult=st.adult,
        item=st.item,
        clue=st.clue,
    )
    return world


def story_text(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    st = world.facts
    mystery: Mystery = st["mystery"]
    setting: Setting = st["setting"]
    return [
        f"Write a gentle whodunit for a young child set in {setting.place} with a little pomp and a useful clue.",
        f"Tell a story where a child notices {mystery.clue_item}, avoids blaming too fast, and gives credit to the kind helper.",
        f"Make a short mystery story about {mystery.missing_item} in {setting.place} that ends with kindness and relief.",
    ]


def story_qa(world: World) -> list[QAItem]:
    st = world.facts
    hero: Entity = st["hero"]
    sidekick: Entity = st["sidekick"]
    adult: Entity = st["adult"]
    mystery: Mystery = st["mystery"]
    setting: Setting = st["setting"]

    return [
        QAItem(
            question=f"Where did {hero.id} notice the first clue?",
            answer=f"{hero.id} noticed the first clue at {setting.place}, near the table and the shiny display.",
        ),
        QAItem(
            question=f"Why did {hero.id} say not to blame anyone yet?",
            answer=f"{hero.id} said not to blame anyone yet because a clue can be kinder than a guess, and the damp marks suggested a careful move instead of a theft.",
        ),
        QAItem(
            question=f"Who got the credit at the end of the story?",
            answer=f"{adult.id} got the credit, because {adult.id} had moved {mystery.missing_item} to keep it safe from the leak.",
        ),
        QAItem(
            question=f"What helped solve the mystery?",
            answer=f"The damp clue, the small note, and {hero.id}'s careful presence of mind helped solve the mystery.",
        ),
        QAItem(
            question=f"How did {hero.id} feel when the missing item was found?",
            answer=f"{hero.id} felt relief and kindness, because the missing item was safe and nobody had been wrongly blamed.",
        ),
        QAItem(
            question=f"Why did the missing item need to be moved?",
            answer=f"It needed to be moved because {mystery.cause}, and the item could have been damaged if it stayed where it was.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    st = world.facts
    mystery: Mystery = st["mystery"]
    out = [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps solve a mystery.",
        ),
        QAItem(
            question="What does credit mean when someone does something helpful?",
            answer="Credit means giving the right person praise for what they did.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a little hint early on about something important that will matter later.",
        ),
        QAItem(
            question="What is caution?",
            answer="Caution means being careful and not rushing into a choice too quickly.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping, sharing, and speaking gently to other people.",
        ),
        QAItem(
            question="What does pomp mean?",
            answer="Pomp means a lot of showy ceremony or grand excitement, like a very fancy event.",
        ),
    ]
    if mystery.id == "trophy":
        out.append(QAItem(question="Why can water be bad for a trophy?", answer="Water can leave spots, make metal tarnish, or damage a shiny trophy if it sits too long." ))
    if mystery.id == "crown":
        out.append(QAItem(question="Why can a paper crown be damaged easily?", answer="A paper crown can crumple or tear if it gets wet or blows around on the floor."))
    if mystery.id == "banner":
        out.append(QAItem(question="Why should a banner be rolled up carefully?", answer="A banner can tear if it drags or gets caught on something, so careful rolling keeps it safe."))
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
        if e.kind == "thing":
            bits.append(f"present={e.present}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    return [(s, m) for s in SETTINGS for m in MYSTERIES]


CURATED = [
    StoryParams(setting="community_hall", mystery="trophy", name="Maya", gender="girl", sidekick="Nina", adult="librarian"),
    StoryParams(setting="library", mystery="crown", name="Owen", gender="boy", sidekick="Eli", adult="janitor"),
    StoryParams(setting="garden_room", mystery="banner", name="Iris", gender="girl", sidekick="June", adult="caretaker"),
]


def explain_rejection(setting: str, mystery: str) -> str:
    return f"(No story: the combination of {setting} and {mystery} does not fit the tiny mystery world.)"


ASP_RULES = r"""
setting(S) :- setting_fact(S).
mystery(M) :- mystery_fact(M).

valid(S,M) :- setting(S), mystery(M), affords(S, ceremony), mystery_tag(M, _).

% The story is reasoned valid when the setting can host the ceremony and the
% mystery has a concrete clue plus a kind resolution.
story_ok(S,M) :- valid(S,M), clue(M,_), resolution(M,_), cause(M,_).

#show valid/2.
#show story_ok/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting_fact", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery_fact", mid))
        lines.append(asp.fact("mystery_tag", mid, m.tag))
        lines.append(asp.fact("clue", mid, m.clue_item))
        lines.append(asp.fact("resolution", mid, m.resolution))
        lines.append(asp.fact("cause", mid, m.cause))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny whodunit storyworld about credit, presence, pomp, foreshadowing, cautionary thinking, and kindness.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--adult", choices=ADULTS)
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
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.mystery:
        combos = [c for c in combos if c[1] == args.mystery]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery = rng.choice(combos)
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(["girl", "boy"])
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    adult = args.adult or rng.choice(ADULTS)
    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, sidekick=sidekick, adult=adult)


def generate(params: StoryParams) -> StorySample:
    st = build_world(params)
    world = tell_story(params)
    return StorySample(
        params=params,
        story=story_text(world),
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, mystery) combos:\n")
        for setting, mystery in combos:
            print(f"  {setting:14} {mystery}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: {p.mystery} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
