#!/usr/bin/env python3
"""
storyworlds/worlds/bend_adenoid_splash_pad_transformation_cautionary_folk.py
=============================================================================

A standalone story world for a small folk-tale cautionary domain set at a splash
pad. A child learns that trying to bend a curious adenoid charm for play can
transform a small, safe game into a slippery problem, and then the world turns
back toward safety through a helper's folk-wisdom warning.

The seed image is a brief tale in the spirit of folk caution:
- children play at a splash pad
- one child wants to bend a strange adenoid charm to make a trick
- the trick backfires as the charm and a painted token transform
- a wise helper warns, rescues, and teaches a safer way

This world models physical meters and emotional memes, supports QA from state,
and includes a small Python/ASP parity twin.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Scene:
    id: str
    place: str
    opening: str
    folk_frame: str
    risk_line: str
    turn_line: str
    safe_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    where: str
    bend_word: str
    tags: set[str] = field(default_factory=set)
    makes_trouble: bool = True


@dataclass
class Transformation:
    id: str
    label: str
    from_word: str
    to_word: str
    trigger: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("troubled", False):
        if "pad" in world.entities and world.get("pad").meters["slick"] < THRESHOLD:
            world.get("pad").meters["slick"] += 1
            out.append("__slick__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    charm = world.entities.get("charm")
    token = world.entities.get("token")
    if not charm or not token:
        return out
    if charm.meters["bent"] >= THRESHOLD and token.meters["painted"] >= THRESHOLD:
        sig = ("transform",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("token").meters["changed"] += 1
            world.get("charm").meters["warped"] += 1
            world.facts["transformed"] = True
            out.append("__transform__")
    return out


def _r_fear(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("transformed") and not world.facts.get("warned"):
        for e in world.entities.values():
            if e.kind == "character":
                e.memes["fear"] += 1
        out.append("__fear__")
    return out


CAUSAL_RULES = [Rule("slip", _r_slip), Rule("transform", _r_transform), Rule("fear", _r_fear)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SCENES = {
    "splash_pad": Scene(
        id="splash_pad",
        place="the splash pad",
        opening="At the splash pad, children laughed under the shining sprays.",
        folk_frame="It felt like a folk village where every fountain sang like a reed pipe.",
        risk_line="But near the stone ring, a small trick could turn playful water into trouble.",
        turn_line="The charm bent wrong, and the painted token seemed to wake and change.",
        safe_image="In the end, the safe spray kept singing while everyone stood dry on the path.",
        tags={"splash_pad", "folk", "caution"},
    )
}

CHAR_NAMES = ["Mara", "Ivo", "Nina", "Pavel", "Sera", "Toma", "Lena", "Rudi"]
TRAITS = ["curious", "careful", "brave", "thoughtful", "restless", "gentle"]

CHARMS = {
    "adenoid": Charm(
        id="adenoid",
        label="adenoid charm",
        phrase="a smooth adenoid charm",
        where="in the pocket of the wooden bench",
        bend_word="bend",
        tags={"adenoid", "bend", "folk"},
    ),
    "reed": Charm(
        id="reed",
        label="reed charm",
        phrase="a thin reed charm",
        where="under the willow basket",
        bend_word="bend",
        tags={"bend", "folk"},
    ),
}

TRANSFORMATIONS = {
    "token_to_fish": Transformation(
        id="token_to_fish",
        label="token-to-fish turning",
        from_word="painted token",
        to_word="silver fish",
        trigger="a bend and a splash",
        tags={"transformation", "folk"},
    ),
    "stone_to_seed": Transformation(
        id="stone_to_seed",
        label="stone-to-seed turning",
        from_word="stone bead",
        to_word="seed pod",
        trigger="a bend and a song",
        tags={"transformation", "folk"},
    ),
}

RESPONSES = {
    "warn_and_fix": Response(
        id="warn_and_fix",
        sense=3,
        power=3,
        text="caught the charm before it slipped, set it straight, and told them to leave the token alone",
        fail="tried to straighten the charm, but the trick had already gone too far",
        qa_text="caught the charm, set it straight, and told them to leave the token alone",
        tags={"caution", "folk"},
    ),
    "wash_and_wait": Response(
        id="wash_and_wait",
        sense=2,
        power=2,
        text="guided them to wash their hands and wait for the water to settle",
        fail="waited too long while the trick kept changing",
        qa_text="guided them to wash their hands and wait for the water to settle",
        tags={"caution"},
    ),
    "low_brow": Response(
        id="low_brow",
        sense=1,
        power=1,
        text="waved at the water and hoped it would settle itself",
        fail="waved at the water, but nothing got better",
        qa_text="waved at the water and hoped it would settle itself",
        tags={"caution"},
    ),
}

KNOWLEDGE = {
    "splash_pad": [("What is a splash pad?", "A splash pad is a place with water sprays for children to play in. It is made for splashing safely.")],
    "bend": [("What does it mean to bend something?", "To bend something means to curve or twist it a little. If you bend the wrong thing, it can break or stop working the way it should.")],
    "adenoid": [("What is an adenoid?", "An adenoid is a small part inside a person's body near the nose and throat. It is not a toy or a plaything.")],
    "transformation": [("What is a transformation?", "A transformation is when something changes into something different. In stories, it can be magical, surprising, or a bit scary.")],
    "caution": [("What does caution mean?", "Caution means being careful because something could go wrong. A cautious person thinks first before acting.")],
    "water": [("Why can wet ground be slippery?", "Wet ground can be slippery because water makes it harder for shoes to grip. That is why children need to walk carefully.")],
}

KNOWLEDGE_ORDER = ["splash_pad", "bend", "adenoid", "transformation", "caution", "water"]


@dataclass
class StoryParams:
    scene: str
    charm: str
    transformation: str
    response: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene_id in SCENES:
        for charm_id in CHARMS:
            for tr_id in TRANSFORMATIONS:
                if scene_id == "splash_pad" and CHARMS[charm_id].makes_trouble:
                    combos.append((scene_id, charm_id, tr_id))
    return combos


def explain_rejection(charm: Charm) -> str:
    return f"(No story: the charm '{charm.label}' is too harmless for this cautionary tale.)"


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(sensible_responses(), key=lambda r: r.sense)


def tell(scene: Scene, charm: Charm, tr: Transformation, response: Response,
         hero_name: str, hero_gender: str, helper_name: str, helper_gender: str,
         parent_type: str, trait: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=[trait], attrs={"scene": scene.id}))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper", traits=["wise"], attrs={"scene": scene.id}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    pad = world.add(Entity(id="pad", type="place", label=scene.place))
    charm_ent = world.add(Entity(id="charm", type="thing", label=charm.label))
    token = world.add(Entity(id="token", type="thing", label=tr.from_word))
    world.facts.update(hero=hero, helper=helper, parent=parent, pad=pad, charm=charm_ent, token=token,
                       scene=scene, charm_cfg=charm, tr_cfg=tr, response=response,
                       warned=False, transformed=False, troubled=True)
    hero.memes["want"] += 1
    helper.memes["care"] += 1
    world.say(scene.opening)
    world.say(scene.folk_frame)
    world.say(f"{hero.id} found {charm.phrase} {charm.where}, and {hero.id} wanted to {charm.bend_word} it for a trick.")
    world.say(f"{hero.id} also held the {tr.from_word}, hoping the bend would make a tiny folk miracle.")
    world.para()
    world.say(scene.risk_line)
    world.say(f"{helper.id} frowned. '{hero.id}, do not {charm.bend_word} an {charm.label}; it is not a plaything.'")
    world.say(f"{helper.id} looked at the water and warned that a wrong bend could start {tr.label}.")
    world.facts["warned"] = True
    if trait in {"careful", "thoughtful", "gentle"}:
        hero.memes["pause"] += 1
    if hero.memes["pause"] < THRESHOLD:
        hero.meters["bent"] += 1
        charm_ent.meters["bent"] += 1
        token.meters["painted"] += 1
        world.say(f"But {hero.id} bent the charm anyway, and the painted token shivered in {world.get('pad').label}.")
        propagate(world, narrate=False)
        world.para()
        world.say(scene.turn_line)
        if world.facts.get("transformed"):
            token.meters["changed"] += 1
            hero.memes["shock"] += 1
            helper.memes["fear"] += 1
            world.say(f"The token turned toward {tr.to_word}, and the splash beside it went strangely still.")
            world.say(f"{helper.id} hurried in and {response.text}.")
            world.say("No one laughed then; they only held their breath and stepped back from the edge of the water.")
        else:
            world.say(f"{helper.id} hurried in and {response.fail}.")
    else:
        world.say(f"{hero.id} stopped with a small gulp and listened, because caution had won.")
        world.say(f"Together they put the charm back and watched the water shimmer without any trick at all.")
    world.para()
    world.say(scene.safe_image)
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    hero.memes["lesson"] += 1
    helper.memes["lesson"] += 1
    world.facts["outcome"] = "transformed" if world.facts.get("transformed") else "averted"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scene = f["scene"]
    charm = f["charm_cfg"]
    tr = f["tr_cfg"]
    return [
        f'Write a folk-tale cautionary story set at {scene.place} that includes the words "{charm.label}" and "bend".',
        f"Tell a small story where {f['hero'].id} tries to bend an {charm.label} near water and a helper warns about transformation.",
        f"Write a child-facing cautionary tale with a splash pad, a strange charm, and a surprising transformation that gets stopped or softened by a wise helper.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    parent = f["parent"]
    charm = f["charm_cfg"]
    tr = f["tr_cfg"]
    resp = f["response"]
    qa = [
        QAItem(
            question=f"Why did {hero.id} go near {world.facts['scene'].place} with the charm?",
            answer=f"{hero.id} wanted to bend the {charm.label} and make a folk trick by the water. The idea felt playful at first, but it could lead to a strange transformation.",
        ),
        QAItem(
            question=f"What did {helper.id} warn about the {charm.label}?",
            answer=f"{helper.id} warned that an {charm.label} was not a toy and should not be bent for a trick. The helper feared that the wrong bend could change the {tr.from_word} into something else.",
        ),
    ]
    if world.facts.get("outcome") == "transformed":
        qa.append(QAItem(
            question=f"What happened when {hero.id} ignored the warning?",
            answer=f"The {tr.from_word} changed, and the splash-pad moment turned uncanny for a breath. Then {helper.id} stepped in and {resp.qa_text}.",
        ))
        qa.append(QAItem(
            question=f"How did the story end after the transformation scare?",
            answer=f"The danger settled, and everyone stayed safe at {world.facts['scene'].place}. The ending image shows a calm splash pad again, which proves the warning mattered.",
        ))
    else:
        qa.append(QAItem(
            question=f"What did {hero.id} do after hearing the warning?",
            answer=f"{hero.id} listened, stopped bending the charm, and put it back. That choice kept the water calm and prevented the transformation from getting started.",
        ))
        qa.append(QAItem(
            question=f"How did {helper.id}'s warning change the ending?",
            answer=f"It helped turn the story back toward safety before the trick could grow. The splash pad stayed bright and ordinary, which is the gentlest ending for a cautionary tale.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["charm_cfg"].tags) | set(world.facts["tr_cfg"].tags) | {"splash_pad", "caution", "water"}
    out: list[QAItem] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(scene="splash_pad", charm="adenoid", transformation="token_to_fish", response="warn_and_fix", hero="Mara", hero_gender="girl", helper="Ivo", helper_gender="boy", parent="mother", trait="careful"),
    StoryParams(scene="splash_pad", charm="reed", transformation="stone_to_seed", response="wash_and_wait", hero="Nina", hero_gender="girl", helper="Pavel", helper_gender="boy", parent="father", trait="curious"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.charm and args.charm in CHARMS and not CHARMS[args.charm].makes_trouble:
        raise StoryError(explain_rejection(CHARMS[args.charm]))
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.charm is None or c[1] == args.charm)
              and (args.transformation is None or c[2] == args.transformation)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene_id, charm_id, tr_id = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    if response not in RESPONSES:
        raise StoryError("Unknown response.")
    hero = args.hero or rng.choice(CHAR_NAMES)
    helper = args.helper or rng.choice([n for n in CHAR_NAMES if n != hero])
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    helper_gender = args.helper_gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(scene=scene_id, charm=charm_id, transformation=tr_id, response=response,
                       hero=hero, hero_gender=hero_gender, helper=helper, helper_gender=helper_gender,
                       parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    scene = SCENES.get(params.scene)
    charm = CHARMS.get(params.charm)
    tr = TRANSFORMATIONS.get(params.transformation)
    resp = RESPONSES.get(params.response)
    if not scene or not charm or not tr or not resp:
        raise StoryError("Invalid params.")
    world = tell(scene, charm, tr, resp, params.hero, params.hero_gender, params.helper, params.helper_gender, params.parent, params.trait)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid(scene,charm,transformation) :- scene(scene), charm(charm), transformation(transformation), scene_ok(scene), charm_trouble(charm).
transformed :- bent, painted, makes_trouble.
warned :- helper_warns.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
        lines.append(asp.fact("scene_ok", sid))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        if c.makes_trouble:
            lines.append(asp.fact("charm_trouble", cid))
    for tid in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", tid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        sample = generate(CURATED[0])
        if not sample.story:
            raise RuntimeError("empty story")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    else:
        print("OK: validation matches and smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale splash-pad cautionary story world.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for x in combos:
            print(" ", x)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
            s = generate(params)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples):
        if idx:
            print("\n" + "=" * 70 + "\n")
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {idx + 1}" if len(samples) > 1 else "")


if __name__ == "__main__":
    main()
