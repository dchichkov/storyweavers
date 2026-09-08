#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class StoryState:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    setting: str
    sailor_name: str
    infantry_name: str
    child_name: str
    seed: Optional[int] = None
    opening: int = 0
    twist: int = 0
    dialogue: int = 0
    ending: int = 0


SETTINGS = {
    "harbor": Setting(place="the harbor", indoor=False, affords={"parade", "lantern", "drum"}),
    "town_square": Setting(place="the town square", indoor=False, affords={"parade", "banner", "drum"}),
    "camp_green": Setting(place="the green camp", indoor=False, affords={"parade", "banner", "lantern"}),
}

SAILOR_NAMES = ["Mina", "Jory", "Lila", "Noah", "Sora", "Beck"]
INFANTRY_NAMES = ["Captain Pine", "Rowan", "Tessa", "Eli", "June", "Ari"]
CHILD_NAMES = ["Pip", "Nora", "Ollie", "Mira", "Leo", "Zia"]

OPENINGS = [
    "At {place}, the parade drums woke the morning while {sailor} and {infantry} checked their uniforms.",
    "The day of the parade had arrived at {place}, and {sailor} the sailor stood beside {infantry} with a smile.",
    "By the edge of {place}, {sailor} the sailor watched the parade line form while {infantry} helped {child} hold a banner.",
    "When the parade bells rang at {place}, {sailor}, a sailor, and {infantry}, an infantry marcher, took their places carefully.",
    "The air at {place} was bright with parade ribbons, and {sailor} the sailor greeted {infantry} before the first march.",
]

TWISTS = [
    "Then a sudden gust lifted the parade map and turned it upside down.",
    "Then the loudest drum rolled once, and every marcher looked the wrong way.",
    "Then a ribbon snagged on {sailor}'s coat and tugged the line into a tiny tangle.",
    "Then {child} whispered that the parade flag was missing its blue corner.",
    "Then a gull stole the shiny parade whistle and flew toward the pier.",
]

DIALOGUE = [
    '"We can still make this lovely," said {infantry}. "Let's slow the line and check the clues."',
    '"I know a sailor trick," {sailor} said. "Tie the loose piece before it can wander."',
    '"Do not worry," {child} said, clutching the banner. "We can fix it together."',
    '"A parade works best when everyone helps," {infantry} said, and {sailor} nodded.',
    '"Look there," said {sailor}. "The answer is not far; it is just hiding in plain sight."',
]

ENDINGS = [
    "Soon the line straightened, the music found its beat again, and the parade went on with extra cheer.",
    "With the little problem solved, the marchers laughed softly and the parade stepped forward like a friend.",
    "By the time the flags lifted again, everyone was smiling, and the parade looked warmer than before.",
    "The crowd clapped as the repaired line passed by, and the harbor felt kind and bright.",
    "In the end, the parade still shone, and the helpers walked home proud of how gently they had fixed it.",
]

ASP_RULES = r"""
#show valid/2.
setting(harbor). setting(town_square). setting(camp_green).
affords(harbor,parade). affords(harbor,lantern). affords(harbor,drum).
affords(town_square,parade). affords(town_square,banner). affords(town_square,drum).
affords(camp_green,parade). affords(camp_green,banner). affords(camp_green,lantern).

valid(P,A) :- affords(P,A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_valid() -> list[tuple]:
    return sorted((p, a) for p, s in SETTINGS.items() for a in s.affords)


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, p = set(asp_valid()), set(python_valid())
    if a != p:
        print("MISMATCH between clingo and python:")
        if a - p:
            print("  only in clingo:", sorted(a - p))
        if p - a:
            print("  only in python:", sorted(p - a))
        return 1
    sample = generate(resolve_params(argparse.Namespace(setting=None, sailor=None, infantry=None, child=None, seed=7), random.Random(7)))
    if "parade" not in sample.story.lower():
        print("Story check failed.")
        return 1
    print(f"OK: clingo gate matches python gate ({len(a)} combos), and story generation works.")
    return 0


def build_world(params: StoryParams) -> StoryState:
    setting = SETTINGS[params.setting]
    world = StoryState(setting=setting)
    sailor = world.add(Entity(id=params.sailor_name, kind="character", type="sailor", traits=["kind", "careful"]))
    infantry = world.add(Entity(id=params.infantry_name, kind="character", type="infantry", traits=["steady", "helpful"]))
    child = world.add(Entity(id=params.child_name, kind="character", type="child", traits=["curious", "bright"]))
    parade = world.add(Entity(id="parade", type="event", label="the parade", owner=None, caretaker=None))

    world.facts["setting_name"] = setting.place
    world.facts["sailor"] = sailor
    world.facts["infantry"] = infantry
    world.facts["child"] = child
    world.facts["parade"] = parade

    world.say(OPENINGS[params.opening % len(OPENINGS)].format(
        place=setting.place, sailor=sailor.id, infantry=infantry.id, child=child.id
    ))
    world.say(f"{sailor.id} noticed the marching boots were nearly ready, and {infantry.id} made sure {child.id} held the banner straight.")
    world.say("The parade felt cheerful already, with drums, ribbons, and polished buttons all waiting for the first step.")

    world.para()
    twist = TWISTS[params.twist % len(TWISTS)].format(sailor=sailor.id, child=child.id)
    world.say(twist)
    world.say(DIALOGUE[params.dialogue % len(DIALOGUE)].format(sailor=sailor.id, infantry=infantry.id, child=child.id))
    world.say(f"{sailor.id} and {infantry.id} looked around together, and {child.id} listened for the best way to help.")
    world.say("The problem was small, but the moment mattered: if they rushed, the parade line would wobble; if they paused, they could fix it kindly.")
    world.say("So they slowed down, used a ribbon knot, and set the loose piece back where it belonged.")
    world.say("The music could breathe again, and the crowd's worried faces turned soft.")

    world.para()
    world.say(f"The twist turned out to be simple: the parade was not broken, just briefly mixed up.")
    world.say(f"{sailor.id} said, \"A parade is a lot like a boat. It moves best when everyone pulls together.\"")
    world.say(f"{infantry.id} answered, \"And a good crew keeps room for a little helper, too.\"")
    world.say(f"{child.id} laughed, then helped carry the banner with both hands.")
    world.say(ENDINGS[params.ending % len(ENDINGS)])
    world.say("By the last drumbeat, the parade had become a warm memory, and the three friends waved as one happy crowd.")

    return world


def generation_prompts(world: StoryState) -> list[str]:
    f = world.facts
    return [
        f"Write a heartwarming story about a parade at {f['setting_name']} with a sailor and infantry helper.",
        f"Tell a small story where {f['sailor'].id}, {f['infantry'].id}, and a child solve a parade twist kindly.",
        "Include dialogue, a twist, and a gentle ending image about the parade becoming safe and cheerful again.",
    ]


def story_qa(world: StoryState) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="Who helped keep the parade calm?",
            answer=f"{f['sailor'].id} the sailor and {f['infantry'].id} the infantry marcher helped keep the parade calm.",
        ),
        QAItem(
            question="What happened in the middle of the story?",
            answer="A small twist disrupted the parade line, but the friends slowed down and fixed it together.",
        ),
        QAItem(
            question="How did the child help?",
            answer=f"{f['child'].id} listened carefully, held the banner, and helped carry it after the problem was solved.",
        ),
        QAItem(
            question="What made the ending heartwarming?",
            answer="Everyone worked together kindly, the parade resumed, and the crowd smiled at the gentle teamwork.",
        ),
    ]


def world_knowledge_qa(world: StoryState) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is a festive group march or procession, often with music, banners, and cheering.",
        ),
        QAItem(
            question="Who is a sailor?",
            answer="A sailor is a person who works on or travels by ships and boats.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers who fight or march on foot.",
        ),
    ]


def dump_trace(world: StoryState) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.caretaker:
            bits.append(f"caretaker={e.caretaker}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    if setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    sailor_name = args.sailor or rng.choice(SAILOR_NAMES)
    infantry_name = args.infantry or rng.choice(INFANTRY_NAMES)
    child_name = args.child or rng.choice(CHILD_NAMES)
    if len({sailor_name, infantry_name, child_name}) < 3:
        raise StoryError("Choose distinct names for sailor, infantry, and child.")
    return StoryParams(
        setting=setting,
        sailor_name=sailor_name,
        infantry_name=infantry_name,
        child_name=child_name,
        seed=args.seed,
        opening=rng.randrange(len(OPENINGS)),
        twist=rng.randrange(len(TWISTS)),
        dialogue=rng.randrange(len(DIALOGUE)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
    ap = argparse.ArgumentParser(description="Heartwarming parade story world with a sailor, infantry, and a twist.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sailor")
    ap.add_argument("--infantry")
    ap.add_argument("--child")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp_valid()
        print(f"{len(model)} valid combinations:\n")
        for place, act in model:
            print(f"  {place:12} {act}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        combos = [(p, SAILOR_NAMES[i % len(SAILOR_NAMES)], INFANTRY_NAMES[i % len(INFANTRY_NAMES)], CHILD_NAMES[i % len(CHILD_NAMES)]) for i, p in enumerate(SETTINGS)]
        for setting, sailor_name, infantry_name, child_name in combos:
            params = StoryParams(setting=setting, sailor_name=sailor_name, infantry_name=infantry_name, child_name=child_name)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
