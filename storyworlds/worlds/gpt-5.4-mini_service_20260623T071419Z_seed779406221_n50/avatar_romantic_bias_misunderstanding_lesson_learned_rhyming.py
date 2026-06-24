#!/usr/bin/env python3
"""
storyworlds/worlds/avatar_romantic_bias_misunderstanding_lesson_learned_rhyming.py
===================================================================================

A standalone storyworld for a tiny rhyming tale about avatar, romantic bias,
a misunderstanding, and a lesson learned.

Premise:
A child loves to help by posting a shiny avatar picture for a romance-themed
class display. But their friend's guess about the picture is biased by a rumor,
so the child is misunderstood. A kind explanation, a small fix, and a lesson
learned turn the awkward moment into a warmer one.

The world keeps typed entities with meters and memes, uses a simple causal
engine, includes an ASP twin, and renders child-facing rhyming prose driven by
the simulated state.
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    label: str
    mood: str


@dataclass
class AvatarGift:
    id: str
    label: str
    phrase: str
    style: str


@dataclass
class Rumor:
    id: str
    label: str
    bias: str
    trigger: str


@dataclass
class Fix:
    id: str
    label: str
    method: str
    promise: str
    lesson: str


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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def rhyme(a: str, b: str) -> str:
    return f"{a} and {b}"


def line(world: World, text: str) -> None:
    world.say(text)


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for ent in list(world.entities.values()):
            if ent.meters.get("hurt", 0) >= THRESHOLD and ("lesson", ent.id) not in world.fired:
                world.fired.add(("lesson", ent.id))
                ent.memes["lesson"] = ent.memes.get("lesson", 0) + 1
                ent.memes["hurt"] = 0
                produced.append(f"{ent.label} learned the truth and felt the gloom grow light.")
                changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_bias(world: World, child: Entity, rumor: Rumor) -> bool:
    sim = world.copy()
    sim.get(child.id).memes["bias"] = sim.get(child.id).memes.get("bias", 0) + 1
    return rumor.bias in {"romantic", "tricky"} and sim.get(child.id).memes["bias"] >= THRESHOLD


def tell(setting: Setting, avatar: AvatarGift, rumor: Rumor, fix: Fix,
         child_name: str, child_type: str, friend_name: str, friend_type: str,
         adult_name: str, adult_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, meters={}, memes={}))
    friend = world.add(Entity(id="friend", kind="character", type=friend_type, label=friend_name, meters={}, memes={}))
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, label=adult_name, meters={}, memes={}))
    pic = world.add(Entity(id="avatar", type="avatar", label=avatar.label, phrase=avatar.phrase, meters={}, memes={}))
    rumor_ent = world.add(Entity(id="rumor", type="rumor", label=rumor.label, phrase=rumor.trigger, meters={}, memes={}))
    fix_ent = world.add(Entity(id="fix", type="fix", label=fix.label, phrase=fix.method, meters={}, memes={}))

    child.memes["kind"] = 1
    friend.memes["bias"] = 1
    adult.memes["warmth"] = 1

    line(world, f"In {setting.place}, by a soft little glow, {child.label} had a bright avatar to show.")
    line(world, f"It was {avatar.phrase}, neat and fine, a sweet little picture with a happy shine.")
    line(world, f"{child.label} hoped it would help with a romance-class card, a tiny display that looked proud and smart.")

    world.para()
    line(world, f"But {friend.label} heard a rumor in the air, and {rumor.label} made {friend.pronoun()} stare.")
    line(world, f"{friend.label} thought the avatar meant something sly, a romantic secret tucked nearby.")

    child.memes["hope"] = 1
    if predict_bias(world, friend, rumor):
        friend.meters["misunderstood"] = 1
        child.meters["hurt"] = 1
        child.memes["sad"] = 1
        line(world, f"{child.label} frowned and felt the sting, for a small misunderstanding can bruise a thing.")
        line(world, f"{adult.label} smiled and said, 'Let's slow this down; a rumor is not a truthy crown.'")
        line(world, f"'{fix.promise},' {adult.label} said, 'and {fix.lesson}.'")
        line(world, f"{child.label} explained the avatar was only for class, not a love note hidden under glass.")
        line(world, f"{friend.label} blushed, then shook {friend.pronoun('possessive')} head; the biased guess was wrong, and the rumor fled.")
        friend.memes["bias"] = 0
        child.meters["hurt"] = 0
        child.memes["joy"] = 1
        adult.memes["pride"] = 1
        world.para()
        line(world, f"So under the moon of the little room light, they set the story straight and made it right.")
        line(world, f"They kept the avatar, plain and bright, and the lesson learned felt warm that night.")
    else:
        line(world, f"But the guess stayed gentle, not bent by blame; the talk was calm, and the meaning stayed the same.")
        line(world, f"{adult.label} nodded, pleased and mild, for honest words can soothe a child.")

    world.facts.update(
        setting=setting,
        avatar=avatar,
        rumor=rumor,
        fix=fix,
        child=child,
        friend=friend,
        adult=adult,
        resolved=True,
    )
    propagate(world, narrate=True)
    return world


SETTINGS = {
    "classroom": Setting(place="the classroom", label="classroom", mood="quiet"),
    "library": Setting(place="the library nook", label="library nook", mood="soft"),
    "playroom": Setting(place="the playroom", label="playroom", mood="cozy"),
}

AVATARS = {
    "smile": AvatarGift(id="smile", label="smiling avatar", phrase="a smiling avatar with a red scarf", style="cheery"),
    "star": AvatarGift(id="star", label="star avatar", phrase="a star-shaped avatar with a gold glow", style="bright"),
    "heart": AvatarGift(id="heart", label="heart avatar", phrase="a little heart avatar in pink and blue", style="sweet"),
}

RUMORS = {
    "rumor": Rumor(id="rumor", label="rumor", bias="romantic", trigger="a romantic rumor"),
    "gossip": Rumor(id="gossip", label="gossip", bias="romantic", trigger="soft gossip"),
    "whisper": Rumor(id="whisper", label="whisper", bias="biased", trigger="a biased whisper"),
}

FIXES = {
    "explain": Fix(id="explain", label="kind explanation", method="explain the picture", promise="No, it's just an avatar for class", lesson="a rumor can twist a harmless thing"),
    "talk": Fix(id="talk", label="gentle talk", method="talk it through", promise="We can ask before we assume", lesson="guessing fast can make hearts feel sore"),
    "share": Fix(id="share", label="clear sharing", method="share the note", promise="Here is the full note", lesson="clear words can chase confusion away"),
}

NAMES = ["Mina", "Noah", "Lia", "Eli", "Pia", "Theo", "Ava", "Ben"]
TRAITS = ["kind", "careful", "bright"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, a, r) for s in SETTINGS for a in AVATARS for r in RUMORS if RUMORS[r].bias == "romantic"]


@dataclass
class StoryParams:
    setting: str
    avatar: str
    rumor: str
    fix: str
    child_name: str
    child_type: str
    friend_name: str
    friend_type: str
    adult_name: str
    adult_type: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="classroom", avatar="heart", rumor="rumor", fix="explain", child_name="Mina", child_type="girl", friend_name="Noah", friend_type="boy", adult_name="Teacher June", adult_type="woman", trait="kind"),
    StoryParams(setting="library", avatar="star", rumor="gossip", fix="talk", child_name="Lia", child_type="girl", friend_name="Eli", friend_type="boy", adult_name="Ms. Fern", adult_type="woman", trait="careful"),
    StoryParams(setting="playroom", avatar="smile", rumor="whisper", fix="share", child_name="Ava", child_type="girl", friend_name="Ben", friend_type="boy", adult_name="Dad", adult_type="father", trait="bright"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming storyworld: avatar, romantic bias, misunderstanding, lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--avatar", choices=AVATARS)
    ap.add_argument("--rumor", choices=RUMORS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.avatar is None or c[1] == args.avatar)
              and (args.rumor is None or c[2] == args.rumor)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, avatar, rumor = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(FIXES))
    child_type = "girl"
    friend_type = "boy"
    adult_type = "woman"
    child_name = args.name or rng.choice(NAMES)
    friend_name = rng.choice([n for n in NAMES if n != child_name])
    adult_name = rng.choice(["Teacher June", "Ms. Fern", "Mom", "Dad"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, avatar=avatar, rumor=rumor, fix=fix,
                       child_name=child_name, child_type=child_type,
                       friend_name=friend_name, friend_type=friend_type,
                       adult_name=adult_name, adult_type=adult_type, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a child in {f["setting"].place} about an {f["avatar"].label} and a {f["rumor"].label}.',
        f"Tell a gentle story where {f['child'].label} is misunderstood because of a romantic bias, then a kind fix helps everyone learn.",
        f'Write a simple lesson-learned story that includes the words "avatar", "romantic", and "bias".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(question=f"Who had the avatar?", answer=f"{f['child'].label} had the avatar and wanted to share it kindly."),
        QAItem(question=f"Why was there a misunderstanding?", answer=f"{f['friend'].label} heard a rumor and let a romantic bias change the guess, so the picture was misunderstood."),
        QAItem(question=f"How did the story end?", answer=f"{f['adult'].label} helped explain the truth, the bias faded, and the lesson learned made the room feel warm again."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a rumor?", answer="A rumor is a story people repeat before they know if it is true."),
        QAItem(question="What is bias?", answer="Bias is when a guess leans one way too quickly instead of being fair."),
        QAItem(question="What does lesson learned mean?", answer="It means someone understands a better way after a mistake or a mix-up."),
    ]


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], AVATARS[params.avatar], RUMORS[params.rumor], FIXES[params.fix],
                 params.child_name, params.child_type, params.friend_name, params.friend_type,
                 params.adult_name, params.adult_type)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world),
                       story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id:8} ({e.type:8}) meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
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


ASP_RULES = r"""
valid(S,A,R) :- setting(S), avatar(A), rumor(R), romantic(R).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for a in AVATARS:
        lines.append(asp.fact("avatar", a))
    for r, rum in RUMORS.items():
        lines.append(asp.fact("rumor", r))
        lines.append(asp.fact("romantic", r) if rum.bias == "romantic" else asp.fact("biased", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show valid/3.")
    model = asp.one_model(program)
    clingo_set = set(asp.atoms(model, "valid"))
    python_set = set(valid_combos())
    if clingo_set != python_set:
        print("Mismatch between ASP and Python.")
        return 1
    print("OK: ASP/Python parity holds.")
    try:
        sample = generate(CURATED[0])
        assert sample.story
    except Exception as exc:
        print(f"Smoke test failed: {exc}")
        return 1
    print("OK: smoke test passed.")
    return 0


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/3."))
        for t in sorted(set(asp.atoms(model, "valid"))):
            print(t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(args.n, 1)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
