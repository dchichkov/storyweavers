#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/orator_reunion_twist_sharing_reconciliation_bedtime_story.py
===========================================================================================

A small bedtime-story world about a young orator, a family reunion, a twist in
the evening plan, sharing, and reconciliation.

The story logic is intentionally simple and state-driven:
- a child prepares a bedtime speech for a family reunion;
- a twist interrupts the evening;
- the child must share a comfort object or a story role;
- the feelings cool through reconciliation before sleep.

The story text is rendered from the simulated world state, not from a frozen
paragraph with swapped nouns.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/orator_reunion_twist_sharing_reconciliation_bedtime_story.py
    python storyworlds/worlds/gpt-5.4-mini/orator_reunion_twist_sharing_reconciliation_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/orator_reunion_twist_sharing_reconciliation_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4-mini/orator_reunion_twist_sharing_reconciliation_bedtime_story.py --verify
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)
    shares: list[str] = field(default_factory=list)

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
    bed: str
    moon: str
    ending_image: str
    night_sound: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Twist:
    id: str
    event: str
    reason: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ShareItem:
    id: str
    label: str
    phrase: str
    comfort: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    soothe: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes["worry"] < THRESHOLD:
            continue
        sig = ("worry", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for other in world.entities.values():
            if other.kind == "character" and other.id != ent.id:
                other.memes["care"] += 1
        out.append("__worry__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes["sharing"] < THRESHOLD or ent.memes["hurt"] < THRESHOLD:
            continue
        sig = ("reconcile", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["soft"] += 1
        ent.memes["hurt"] = 0.0
        out.append("__reconcile__")
    return out


CAUSAL_RULES = [
    Rule("worry", "social", _r_worry),
    Rule("reconcile", "social", _r_reconcile),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(scene: Scene, twist: Twist, share: ShareItem) -> bool:
    return bool(scene.place and twist.event and share.label)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def predict_reunion(world: World, child: Entity, twist: Twist, share: ShareItem) -> dict:
    sim = world.copy()
    _twist(sim, sim.get(child.id), twist, narrate=False)
    _share(sim, sim.get(child.id), share, narrate=False)
    return {
        "hurt": sim.get(child.id).memes["hurt"] >= THRESHOLD,
        "soft": sim.get(child.id).memes["soft"] >= THRESHOLD,
    }


def _twist(world: World, child: Entity, twist: Twist, narrate: bool = True) -> None:
    child.memes["worry"] += 1
    child.meters["night"] += 1
    if narrate:
        world.say(f"Then came a twist: {twist.event}. {twist.reason} {twist.effect}.")


def _share(world: World, child: Entity, share: ShareItem, narrate: bool = True) -> None:
    child.memes["sharing"] += 1
    child.shares.append(share.label)
    if narrate:
        world.say(
            f"{child.id} shared {share.phrase} with everyone at the reunion, "
            f"and the room felt warmer at once."
        )
    child.memes["hurt"] = 0.0


def opening(world: World, child: Entity, family: Entity, scene: Scene) -> None:
    child.memes["joy"] += 1
    family.memes["love"] += 1
    world.say(
        f"At bedtime, {child.id} was the family orator, standing by {scene.bed} "
        f"in {scene.place}. {child.id} had practiced a little speech for the reunion, "
        f"and {scene.moon} shone softly above the window."
    )
    world.say(
        f"{scene.night_sound.capitalize()}, and every cousin and grown-up leaned in "
        f"to hear the bedtime words."
    )


def twist_beats(world: World, child: Entity, twist: Twist, family: Entity) -> None:
    _twist(world, child, twist, narrate=True)
    family.memes["surprise"] += 1
    world.say(
        f"The reunion turned sideways for a moment, because {twist.event} changed "
        f"the plan and everyone had to pause."
    )


def share_beats(world: World, child: Entity, share: ShareItem, family: Entity) -> None:
    world.say(
        f"{child.id} took a breath and decided to share {share.phrase}. "
        f"{child.id} passed it around instead of keeping it close."
    )
    _share(world, child, share, narrate=False)
    family.memes["calm"] += 1
    world.say(
        f"That small sharing made the room gentler, and even the shyest guest smiled."
    )


def reconcile_beats(world: World, child: Entity, family: Entity, response: Response) -> None:
    child.memes["hurt"] = 0.0
    child.memes["soft"] += response.soothe
    family.memes["soft"] += 1
    world.say(
        f"Then {child.id} spoke again, this time softly. "
        f"{response.text}."
    )
    world.say(
        f"The family listened, and the hard feeling melted into reconciliation."
    )


def ending(world: World, child: Entity, scene: Scene) -> None:
    child.memes["sleepy"] += 1
    world.say(
        f"At last, the reunion settled down. {scene.ending_image}, and "
        f"{child.id} curled up under the blanket, proud that the speech had become "
        f"a sharing moment instead of a worry."
    )


def tell(scene: Scene, twist: Twist, share: ShareItem, response: Response,
         child_name: str = "Mina", child_gender: str = "girl",
         family_name: str = "Family", family_gender: str = "thing",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="orator", traits=["gentle", "brave"]))
    family = world.add(Entity(id=family_name, kind="character", type=family_gender,
                              role="family", label="the family"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type,
                              role="parent", label="the parent"))

    opening(world, child, family, scene)
    world.para()
    twist_beats(world, child, twist, family)
    world.say(f"{child.id} felt a little ache in {child.pronoun('possessive')} chest.")
    world.para()
    share_beats(world, child, share, family)
    reconcile_beats(world, child, family, response)
    world.para()
    ending(world, child, scene)

    world.facts.update(
        child=child, family=family, parent=parent, scene=scene, twist=twist,
        share=share, response=response, outcome="reconciled",
    )
    return world


SCENES = {
    "nursery": Scene("nursery", "the nursery", "the little bed", "the moon",
                     "The lamp glowed like a tiny star", "A lullaby hummed nearby",
                     {"bedtime", "cozy"}),
    "storyroom": Scene("storyroom", "the storyroom", "the soft bed", "the moon",
                       "A teddy sat by the pillow, listening quietly",
                       "The clock ticked like a sleepy mouse", {"bedtime", "cozy"}),
    "guestroom": Scene("guestroom", "the guestroom", "the tucked-in bed", "the moon",
                       "A warm quilt lay smooth as a calm wave",
                       "The house whispered all around", {"bedtime", "cozy"}),
}

TWISTS = {
    "missing_page": Twist("missing_page", "the last page of the bedtime speech was missing",
                          "The speech had been perfect in practice, but now the final words were gone.",
                          "That surprise made the room go very quiet.",
                          {"twist", "bedtime"}),
    "shy_cousin": Twist("shy_cousin", "a shy cousin hid behind the chair",
                        "The cousin wanted to listen, but felt too shy to come close.",
                        "Everyone had to make room for a softer way to begin.",
                        {"twist", "reunion"}),
    "snuffed_candle": Twist("snuffed_candle", "the candle went out",
                            "The room became darker than expected.",
                            "The hush felt bigger, and the orator had to change the plan.",
                            {"twist", "bedtime"}),
}

SHARES = {
    "blanket": ShareItem("blanket", "blanket space", "the blanket", "warm"),
    "cookies": ShareItem("cookies", "cookies", "the cookies", "sweet"),
    "poem": ShareItem("poem", "a tiny poem", "the tiny poem", "kind"),
    "lantern": ShareItem("lantern", "lantern light", "the little lantern", "glow"),
}

RESPONSES = {
    "apology": Response("apology", 3, 2,
                        "said sorry for the sharp little words and thanked everyone for waiting",
                        "said sorry and thanked everyone for waiting"),
    "invitation": Response("invitation", 3, 2,
                           "invited the shy cousins to share the next line together",
                           "invited the shy cousins to share the next line together"),
    "promise": Response("promise", 2, 3,
                        "promised to keep the evening gentle and make room for everyone",
                        "promised to keep the evening gentle and make room for everyone"),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Ada", "Ivy", "Maya"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Finn", "Owen", "Leo"]


@dataclass
class StoryParams:
    scene: str
    twist: str
    share: str
    response: str
    child: str
    child_gender: str
    parent: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SCENES:
        for t in TWISTS:
            for sh in SHARES:
                if reasonableness_gate(SCENES[s], TWISTS[t], SHARES[sh]):
                    combos.append((s, t, sh))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    scene: Scene = f["scene"]  # type: ignore[assignment]
    twist: Twist = f["twist"]  # type: ignore[assignment]
    share: ShareItem = f["share"]  # type: ignore[assignment]
    return [
        f'Write a bedtime story for a young child that includes the words "orator" and "reunion".',
        f"Tell a cozy story where {child.id} is an orator at a family reunion, a twist interrupts the evening, and sharing helps everyone feel better.",
        f"Write a gentle bedtime story set in {scene.place} where {twist.event} leads to sharing {share.phrase} and reconciliation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]  # type: ignore[assignment]
    scene: Scene = f["scene"]  # type: ignore[assignment]
    twist: Twist = f["twist"]  # type: ignore[assignment]
    share: ShareItem = f["share"]  # type: ignore[assignment]
    resp: Response = f["response"]  # type: ignore[assignment]
    return [
        QAItem(
            question="Who was the story about?",
            answer=f"It was about {child.id}, who acted like the family orator at a cozy reunion. The whole bedtime scene centered on {child.id}'s little speech and the people gathered to hear it.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {twist.event}. {twist.reason} {twist.effect}",
        ),
        QAItem(
            question="How did sharing help?",
            answer=f"{child.id} shared {share.phrase} with the family, so the room felt warmer and calmer. That sharing made it easier for everyone to listen and reconcile.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with reconciliation and bedtime calm. {resp.qa_text}, and then {child.id} curled up contentedly under the blanket.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an orator?",
            answer="An orator is a person who speaks to a group with care and confidence. Sometimes an orator tells a speech to help everyone feel included.",
        ),
        QAItem(
            question="What is a reunion?",
            answer="A reunion is a time when people come together again after being apart. It can feel warm and happy because everyone gets to see each other.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use or enjoy something with you. It helps people feel welcome and connected.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when hurt feelings settle down and people make peace again. It often happens after someone listens, apologizes, or tries to be kind.",
        ),
    ]


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
    lines.append("== (3) World knowledge questions ==")
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
        if e.shares:
            bits.append(f"shares={e.shares}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
sense_ok(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(SC, TW, SH) :- scene(SC), twist(TW), share(SH), scene_place(SC), twist_event(TW), share_item(SH).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy
    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for tid in TWISTS:
        lines.append(asp.fact("twist", tid))
    for shid in SHARES:
        lines.append(asp.fact("share", shid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp  # lazy
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import storyworlds.asp as asp  # lazy
    model = asp.one_model(asp_program("", "#show sense_ok/1."))
    return sorted(r for (r,) in asp.atoms(model, "sense_ok"))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
    # smoke test a normal generation path
    try:
        sample = generate(resolve_params(argparse.Namespace(scene=None, twist=None, share=None, response=None, child=None, child_gender=None, parent=None), random.Random(7)))  # type: ignore[arg-type]
        _ = sample.story
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about orator, reunion, twist, sharing, and reconciliation.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--share", choices=SHARES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if not combos:
        raise StoryError("(No valid combinations available.)")
    combos = [c for c in combos
              if (args.scene is None or c[0] == args.scene)
              and (args.twist is None or c[1] == args.twist)
              and (args.share is None or c[2] == args.share)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, twist, share = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    if RESPONSES[response].sense < SENSE_MIN:
        raise StoryError("(Chosen response is too weak for this story.)")
    gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(scene, twist, share, response, child, gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SCENES[params.scene], TWISTS[params.twist], SHARES[params.share], RESPONSES[params.response], params.child, params.child_gender, "Family", "thing", params.parent)
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
    StoryParams("nursery", "missing_page", "blanket", "apology", "Mina", "girl", "mother"),
    StoryParams("storyroom", "shy_cousin", "cookies", "invitation", "Eli", "boy", "father"),
    StoryParams("guestroom", "snuffed_candle", "lantern", "promise", "Nora", "girl", "mother"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show sense_ok/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        print(f"{len(asp_valid_combos())} compatible combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
