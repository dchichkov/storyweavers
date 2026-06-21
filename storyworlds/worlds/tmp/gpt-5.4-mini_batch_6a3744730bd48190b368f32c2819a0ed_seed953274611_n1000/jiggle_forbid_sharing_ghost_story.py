#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/jiggle_forbid_sharing_ghost_story.py
=====================================================================

A small storyworld for a ghost-story-style sharing tale: one child wants to
share a special toy or treat, the rules say to forbid a bad choice, and the
solution is a kinder sharing swap. The world keeps the action concrete by
tracking physical objects and emotional state, then renders a child-facing
story with a spooky-but-gentle mood.

Seed words:
- jiggle
- forbid

Feature:
- Sharing

Style:
- Ghost Story
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
FORBID_MIN = 3
SHARE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: {"shake": 0.0, "spook": 0.0, "warmth": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"want": 0.0, "fear": 0.0, "care": 0.0, "pride": 0.0})

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
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    dark_spot: str


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    kind: str
    can_share: bool = True
    can_jiggle: bool = False
    spooks: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Choice:
    id: str
    sense: int
    share_gain: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


@dataclass
class StoryParams:
    setting: str
    child: str
    child_type: str
    helper: str
    helper_type: str
    object: str
    choice: str
    seed: Optional[int] = None


SETTINGS = {
    "attic": Setting(id="attic", place="an old attic", mood="dusty and quiet", dark_spot="the corner by the trunk"),
    "hall": Setting(id="hall", place="a narrow hallway", mood="cold and whispery", dark_spot="the space under the stairs"),
    "garden": Setting(id="garden", place="a moonlit garden", mood="soft and silver", dark_spot="the shadow under the bench"),
}

THINGS = {
    "jack_in_box": Thing(id="jack_in_box", label="jack-in-the-box", phrase="a squeaky jack-in-the-box", kind="toy", can_share=True, can_jiggle=True, tags={"toy", "jiggle"}),
    "lantern": Thing(id="lantern", label="lantern", phrase="a little lantern", kind="light", can_share=True, can_jiggle=False, tags={"light"}),
    "cookie": Thing(id="cookie", label="cookie", phrase="a sugar cookie", kind="snack", can_share=True, can_jiggle=False, tags={"snack", "share"}),
    "radio": Thing(id="radio", label="radio", phrase="an old radio", kind="toy", can_share=False, can_jiggle=True, spooks=True, tags={"toy", "spook"}),
}

CHOICES = {
    "share_cookie": Choice(id="share_cookie", sense=3, share_gain=2,
                           text="broke the cookie in two and offered a half to {helper}",
                           fail="tried to share the cookie, but it crumbled into crumbs",
                           qa_text="broke the cookie in two and shared it kindly",
                           tags={"share"}),
    "share_light": Choice(id="share_light", sense=4, share_gain=3,
                          text="held the lantern low so both of them could see",
                          fail="held the lantern too low and still could not make the dark place feel safe",
                          qa_text="used the lantern together and made the dark place feel safer",
                          tags={"light", "share"}),
    "forbid_radio": Choice(id="forbid_radio", sense=5, share_gain=0,
                           text="said the radio was too spooky to share and should stay quiet",
                           fail="forgot to forbid the radio, and its crackle made the shadows jump",
                           qa_text="forbade the spooky radio and kept the room calm",
                           tags={"forbid", "spook"}),
}

NAMES_GIRL = ["Mina", "Lily", "June", "Nora", "Maya"]
NAMES_BOY = ["Theo", "Ben", "Finn", "Eli", "Noah"]


def is_reasonable(obj: Thing, choice: Choice) -> bool:
    if choice.id == "share_cookie":
        return obj.can_share and obj.kind == "snack"
    if choice.id == "share_light":
        return obj.can_share and obj.kind == "light"
    if choice.id == "forbid_radio":
        return obj.spooks
    return False


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for thing_id, thing in THINGS.items():
        for choice_id, choice in CHOICES.items():
            if is_reasonable(thing, choice):
                combos.append((thing_id, choice_id))
    return combos


def reason_reject(thing: Thing, choice: Choice) -> str:
    if choice.id == "forbid_radio" and not thing.spooks:
        return f"(No story: {thing.label} is not spooky enough to need forbidding.)"
    if choice.id == "share_cookie" and thing.kind != "snack":
        return f"(No story: {thing.label} is not a snack, so sharing it as food would not fit.)"
    if choice.id == "share_light" and thing.kind != "light":
        return f"(No story: {thing.label} is not a light, so both children could not share it that way.)"
    return "(No story: this pairing does not make a sensible ghost-story sharing problem.)"


def sensible_choices() -> list[Choice]:
    return [c for c in CHOICES.values() if c.sense >= FORBID_MIN or c.id != "share_cookie"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.object and args.choice:
        thing = THINGS[args.object]
        choice = CHOICES[args.choice]
        if not is_reasonable(thing, choice):
            raise StoryError(reason_reject(thing, choice))
    combos = [c for c in valid_combos()
              if (args.object is None or c[0] == args.object)
              and (args.choice is None or c[1] == args.choice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    obj_id, choice_id = rng.choice(sorted(combos))
    setting = args.setting or rng.choice(sorted(SETTINGS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or ("boy" if child_type == "girl" else "girl")
    return StoryParams(
        setting=setting,
        child=args.child or rng.choice(NAMES_GIRL if child_type == "girl" else NAMES_BOY),
        child_type=child_type,
        helper=args.helper or rng.choice(NAMES_GIRL if helper_type == "girl" else NAMES_BOY),
        helper_type=helper_type,
        object=obj_id,
        choice=choice_id,
    )


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    thing = THINGS[params.object]
    choice = CHOICES[params.choice]
    world = World(setting)
    child = world.add(Entity(id=params.child, kind="character", type=params.child_type, role="child"))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type, role="helper"))
    object_ent = world.add(Entity(id="object", kind="thing", type=thing.kind, label=thing.label, attrs={"phrase": thing.phrase}))
    child.memes["want"] = 2.0
    helper.memes["care"] = 1.0
    world.say(
        f"That night, in {setting.place}, the air felt {setting.mood}. "
        f"{child.id} and {helper.id} stood near {setting.dark_spot}, where the shadows seemed to listen."
    )
    world.say(
        f"{child.id} spotted {thing.phrase} and gave it a little jiggle. "
        f"The toy shivered, and the room answered with a tiny, spooky creak."
    )
    world.para()
    world.say(
        f"{child.id} wanted to share it, but {helper.id} remembered a rule and spoke softly."
    )
    if choice.id == "forbid_radio":
        helper.memes["fear"] += 1
        world.say(
            f'"We must forbid the radio," {helper.id} whispered, "because its crackle makes the dark feel mean."'
        )
        world.say(
            f"{child.id} looked at the radio, nodded, and left it alone."
        )
        world.say(
            f"Then they chose the lantern instead, and the dark spot became only a shadow, not a scare."
        )
        helper.meters["warmth"] += 1
    elif choice.id == "share_cookie":
        child.memes["pride"] += 1
        helper.meters["warmth"] += 1
        world.say(
            f"{child.id} {choice.text.format(helper=helper.id)}."
        )
        world.say(
            f"{helper.id} smiled, and the two halves made a smaller but sweeter snack for both of them."
        )
    else:
        child.meters["warmth"] += 1
        helper.meters["warmth"] += 1
        world.say(
            f"{child.id} and {helper.id} {choice.text.format(helper=helper.id)}."
        )
        world.say(
            f"The light did not banish the dark, but it made the room feel like a safe place to keep sharing stories."
        )
    world.para()
    world.say(
        f"In the end, the shadows stayed in their corner, and {child.id} had a brighter, kinder night."
    )
    world.facts.update(setting=setting, child=child, helper=helper, thing=thing, choice=choice, object_ent=object_ent)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the words "jiggle" and "forbid".',
        f"Tell a spooky-but-safe sharing story where {f['child'].id} gives something to {f['helper'].id} and a grown-up rule says to forbid the spooky choice.",
        f'Write a night-time story in a ghost-story mood where two children hear a little creak, choose a kinder way to share, and keep the dark from feeling scary.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, helper, thing, choice = f["child"], f["helper"], f["thing"], f["choice"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {helper.id}, who were standing in a dark place and trying to decide what to do with {thing.phrase}."),
        ("Why did the room feel spooky?",
         f"The setting was {world.setting.mood}, and the shadows near {world.setting.dark_spot} seemed to listen. "
         f"The little jiggle made the quiet place sound even more mysterious."),
        ("What did they do instead of making things worse?",
         f"They chose to {choice.qa_text}. That kept the night calm and let them share without turning the dark into a bigger scare."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["thing"].tags) | set(f["choice"].tags)
    out = []
    if "jiggle" in tags:
        out.append(("What does it mean to jiggle something?",
                    "To jiggle something is to shake it lightly back and forth. It can make a toy rattle or wobble a little bit."))
    if "forbid" in tags:
        out.append(("What does forbid mean?",
                    "To forbid means to say something is not allowed. A grown-up uses that word when a choice is too risky or not right."))
    if "share" in tags:
        out.append(("What does sharing mean?",
                    "Sharing means letting someone else use or have part of something. It is a kind way to help both people enjoy it."))
    if "spook" in tags:
        out.append(("Why can a spooky sound feel scary?",
                    "A spooky sound can feel scary when it happens in a quiet dark place. People imagine something hiding there, even if it is only a creak."))
    if "light" in tags:
        out.append(("What can a lantern do?",
                    "A lantern gives off light so people can see in the dark. It can make a room feel safer and less strange."))
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Obj, Choice) :- thing(Obj), choice(Choice), reasonable(Obj, Choice).
story(Obj, Choice) :- valid(Obj, Choice).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, thing in THINGS.items():
        lines.append(asp.fact("thing", tid))
        if thing.can_share:
            lines.append(asp.fact("can_share", tid))
        if thing.can_jiggle:
            lines.append(asp.fact("can_jiggle", tid))
        if thing.spooks:
            lines.append(asp.fact("spooks", tid))
        for tag in sorted(thing.tags):
            lines.append(asp.fact("tag", tid, tag))
    for cid, choice in CHOICES.items():
        lines.append(asp.fact("choice", cid))
        lines.append(asp.fact("sense", cid, choice.sense))
        if choice.id == "forbid_radio":
            lines.append(asp.fact("forbid", cid))
        if choice.id.startswith("share"):
            lines.append(asp.fact("share", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between clingo and valid_combos()")
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        assert sample.story
        _ = format_qa(sample)
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and story smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story sharing world with jiggle and forbid.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=THINGS)
    ap.add_argument("--choice", choices=CHOICES)
    ap.add_argument("--child")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.object not in THINGS or params.choice not in CHOICES:
        raise StoryError("Invalid story parameters.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


CURATED = [
    StoryParams(setting="attic", child="Mina", child_type="girl", helper="Theo", helper_type="boy", object="radio", choice="forbid_radio"),
    StoryParams(setting="hall", child="Eli", child_type="boy", helper="Nora", helper_type="girl", object="cookie", choice="share_cookie"),
    StoryParams(setting="garden", child="Lily", child_type="girl", helper="Ben", helper_type="boy", object="lantern", choice="share_light"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.object and args.choice:
        if not is_reasonable(THINGS[args.object], CHOICES[args.choice]):
            raise StoryError(reason_reject(THINGS[args.object], CHOICES[args.choice]))
    combos = [c for c in valid_combos()
              if (args.object is None or c[0] == args.object)
              and (args.choice is None or c[1] == args.choice)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    obj_id, choice_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or ("boy" if child_type == "girl" else "girl")
    return StoryParams(
        setting=args.setting or rng.choice(sorted(SETTINGS)),
        child=args.child or rng.choice(NAMES_GIRL if child_type == "girl" else NAMES_BOY),
        child_type=child_type,
        helper=args.helper or rng.choice(NAMES_GIRL if helper_type == "girl" else NAMES_BOY),
        helper_type=helper_type,
        object=obj_id,
        choice=choice_id,
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for a, b in combos:
            print(f"  {a:12} {b}")
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random((args.seed or 0) + i))
            p.seed = (args.seed or 0) + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
