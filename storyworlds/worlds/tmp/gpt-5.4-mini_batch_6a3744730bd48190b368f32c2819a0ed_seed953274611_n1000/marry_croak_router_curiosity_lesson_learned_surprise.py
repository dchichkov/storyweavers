#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/marry_croak_router_curiosity_lesson_learned_surprise.py
======================================================================================

A small bedtime-story world about a curious child, a sleepy home, a noisy router,
a froggy toy that croaks, and a surprising lesson about not rushing to "fix"
grown-up things. The world supports a cozy premise, a curiosity-driven turn, a
surprise, and a calm lesson learned ending.

The story grows from world state:
- a child notices a blinking router light and gets curious
- a little croak/sound comes from a toy frog near the router shelf
- a surprise reveals a wedding invitation / family plan / promise
- a grown-up gently explains the router is not a toy
- the child learns a bedtime-safe lesson and the room ends peaceful

This file is self-contained and stdlib-only for prose generation.
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
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class StoryParams:
    child_name: str
    child_gender: str
    adult_name: str
    adult_gender: str
    room: str
    curiosity_object: str
    surprise_kind: str
    seed: Optional[int] = None


@dataclass
class Setting:
    id: str
    label: str
    cozy_detail: str
    twilight_detail: str
    router_place: str


@dataclass
class Curiosity:
    id: str
    prompt: str
    wonder: str
    tug: str
    topic: str


@dataclass
class Surprise:
    id: str
    reveal: str
    object_label: str
    object_phrase: str
    effect: str


@dataclass
class Lesson:
    id: str
    text: str
    safe_alternative: str
    closing_image: str


class World:
    def __init__(self) -> None:
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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_curious(world: World) -> list[str]:
    out = []
    child = world.get("child")
    router = world.get("router")
    if child.memes["curiosity"] < THRESHOLD:
        return out
    sig = ("curious",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    router.meters["noticed"] += 1
    child.memes["wonder"] += 1
    out.append("__curious__")
    return out


def _r_noise(world: World) -> list[str]:
    out = []
    frog = world.get("frog")
    if frog.meters["croak"] < THRESHOLD:
        return out
    sig = ("noise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").memes["alarm"] += 1
    out.append("__croak__")
    return out


def _r_soft_lesson(world: World) -> list[str]:
    out = []
    if world.get("adult").memes["calm"] < THRESHOLD:
        return out
    sig = ("lesson",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["relief"] += 1
    out.append("__lesson__")
    return out


CAUSAL_RULES = [Rule("curious", _r_curious), Rule("noise", _r_noise), Rule("lesson", _r_soft_lesson)]


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


def reasonable_choice(curiosity: Curiosity, surprise: Surprise) -> bool:
    return curiosity.topic in {"router", "frog", "wedding"} and surprise.id in SURPRISES


def predict_result(world: World) -> dict:
    sim = world.copy()
    sim.get("child").memes["curiosity"] += 1
    sim.get("frog").meters["croak"] += 1
    propagate(sim, narrate=False)
    return {
        "noticed_router": sim.get("router").meters["noticed"] >= THRESHOLD,
        "alarm": sim.get("room").memes["alarm"] >= THRESHOLD,
    }


def setup(world: World, setting: Setting, child: Entity, adult: Entity) -> None:
    child.memes["curiosity"] = 1.0
    child.memes["joy"] = 1.0
    adult.memes["calm"] = 1.0
    adult.memes["love"] = 1.0
    world.say(
        f"At bedtime, {child.id} and {adult.id} were in {setting.label}. "
        f"{setting.cozy_detail} {setting.twilight_detail}"
    )


def curiosity_turn(world: World, child: Entity, curiosity: Curiosity, router: Entity) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"{child.id} pointed at the {router.label}. {curiosity.prompt} "
        f"{curiosity.wonder} {curiosity.tug}"
    )


def croak_event(world: World, frog: Entity, router: Entity) -> None:
    frog.meters["croak"] += 1
    router.meters["light"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the little toy frog near the shelf went croak, and the router's "
        f"tiny light blinked twice as if it had heard the sound."
    )


def surprise_reveal(world: World, adult: Entity, surprise: Surprise) -> None:
    adult.memes["surprise"] += 1
    world.say(
        f"{adult.id} smiled and showed {surprise.object_phrase}. "
        f"{surprise.reveal} {surprise.effect}"
    )


def lesson_scene(world: World, adult: Entity, child: Entity, lesson: Lesson, router: Entity) -> None:
    child.memes["lesson_learned"] += 1
    child.memes["curiosity"] -= 0.25
    world.say(
        f"{adult.id} tucked {child.id} in close and said, "
        f"\"{lesson.text} {lesson.safe_alternative}\""
    )
    world.say(
        f"{child.id} nodded, and the {router.label} stayed quiet on its shelf "
        f"while the room turned soft and still."
    )
    world.say(lesson.closing_image)


def tell(setting: Setting, curiosity: Curiosity, surprise: Surprise, lesson: Lesson,
         child_name: str = "Mia", child_gender: str = "girl",
         adult_name: str = "Mom", adult_gender: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    adult = world.add(Entity(id=adult_name, kind="character", type=adult_gender, role="adult"))
    room = world.add(Entity(id="room", type="room", label=setting.label))
    router = world.add(Entity(id="router", kind="thing", type="thing", label="router"))
    frog = world.add(Entity(id="frog", kind="thing", type="thing", label="toy frog"))
    gift = world.add(Entity(id="gift", kind="thing", type="thing", label=surprise.object_label))
    world.facts["room"] = room
    world.facts["router"] = router
    world.facts["frog"] = frog
    world.facts["gift"] = gift

    setup(world, setting, child, adult)
    world.para()
    curiosity_turn(world, child, curiosity, router)
    croak_event(world, frog, router)
    surprise_reveal(world, adult, surprise)
    world.para()
    lesson_scene(world, adult, child, lesson, router)

    world.facts.update(
        child=child,
        adult=adult,
        setting=setting,
        curiosity=curiosity,
        surprise=surprise,
        lesson=lesson,
        noticed_router=router.meters["noticed"] >= THRESHOLD,
        croaked=frog.meters["croak"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "bedroom": Setting(
        id="bedroom",
        label="the bedroom",
        cozy_detail="A blanket was tucked high on the pillow, and the lamp made a honey glow.",
        twilight_detail="Outside, the stars were already pinpricks in the sky.",
        router_place="on the dresser",
    ),
    "living_room": Setting(
        id="living_room",
        label="the living room",
        cozy_detail="A little pillow fort waited by the rug, and a night-light shone by the wall.",
        twilight_detail="The curtains were sleepy and blue in the dark.",
        router_place="on the shelf",
    ),
    "hallway": Setting(
        id="hallway",
        label="the hallway nook",
        cozy_detail="A wooly rug made the floor feel warm, and a lamp hummed like a lullaby.",
        twilight_detail="The house had the quiet kind of hush that comes before dreams.",
        router_place="beside the small table",
    ),
}

CURIOSITIES = {
    "router": Curiosity("router", "A blinking light caught the child's eye.", "Why does it blink?", "It looked like a tiny star.", "router"),
    "frog": Curiosity("frog", "A funny croak sounded from the corner.", "What made that little croak?", "It seemed to be calling for attention.", "frog"),
    "wedding": Curiosity("wedding", "A ribboned envelope peeked out of a book.", "Who is the wedding for?", "It felt like a surprise waiting to be opened.", "wedding"),
}

SURPRISES = {
    "marry": Surprise(
        id="marry",
        reveal="It was an invitation to a wedding, where two grown-ups would marry and share a happy promise.",
        object_label="a ribboned invitation",
        object_phrase="a ribboned invitation with gold corners",
        effect="The room felt extra warm, as if a new kind of family sunshine had arrived.",
    ),
    "gift": Surprise(
        id="gift",
        reveal="It was a surprise gift for the child, wrapped in blue paper and tied with string.",
        object_label="a wrapped parcel",
        object_phrase="a wrapped parcel with a bow",
        effect="The child gasped because bedtime had turned into a tiny celebration.",
    ),
    "note": Surprise(
        id="note",
        reveal="It was a note that said goodnight and mentioned a small family plan for tomorrow.",
        object_label="a folded note",
        object_phrase="a folded note tucked into a book",
        effect="The words made the child smile, because tomorrow suddenly felt gentle and bright.",
    ),
}

LESSONS = {
    "router": Lesson(
        id="router",
        text="The router is for sending messages through the house, not for little hands to tinker with.",
        safe_alternative="If you are curious, you can ask a grown-up to show you the blinking light and then use your own imagination for the rest.",
        closing_image="The router blinked calmly, like a sleepy little watchman, and the child drifted toward dreams.",
    ),
    "frog": Lesson(
        id="frog",
        text="When something strange croaks in the dark, the safest thing is to ask a grown-up instead of poking it.",
        safe_alternative="You can listen, wonder, and let a helper explain.",
        closing_image="The toy frog sat still in the moonlight, and everything felt safe again.",
    ),
    "marry": Lesson(
        id="marry",
        text="Big promises are for grown-ups, but children can still enjoy the happy news and the love around it.",
        safe_alternative="You can watch the preparations, smile, and ask gentle questions.",
        closing_image="The invitation rested on the table like a little treasure, and the whole room seemed to breathe softly.",
    ),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for cid in CURIOSITIES:
            for spid in SURPRISES:
                if reasonable_choice(CURIOSITIES[cid], SURPRISES[spid]):
                    combos.append((sid, cid, spid))
    return combos


def explain_rejection(curiosity: Curiosity, surprise: Surprise) -> str:
    return f"(No story: the chosen curiosity '{curiosity.id}' and surprise '{surprise.id}' do not fit this bedtime lesson.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime-story world about curiosity, a croaking toy, a router, and a surprise.")
    ap.add_argument("--room", choices=SETTINGS)
    ap.add_argument("--curiosity", choices=CURIOSITIES)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--name")
    ap.add_argument("--adult")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult-gender", choices=["woman", "man", "aunt", "uncle", "mom", "dad"])
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
    if args.curiosity and args.surprise:
        if not reasonable_choice(CURIOSITIES[args.curiosity], SURPRISES[args.surprise]):
            raise StoryError(explain_rejection(CURIOSITIES[args.curiosity], SURPRISES[args.surprise]))
    combos = [c for c in valid_combos()
              if (args.room is None or c[0] == args.room)
              and (args.curiosity is None or c[1] == args.curiosity)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    room, curiosity, surprise = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(["Mia", "Luna", "Ivy", "Noah", "Eli", "Theo"])
    adult_gender = args.adult_gender or rng.choice(["woman", "man", "aunt", "uncle"])
    adult_name = args.adult or rng.choice(["Mom", "Dad", "Aunt June", "Uncle Ben"])
    return StoryParams(
        child_name=child_name,
        child_gender=child_gender,
        adult_name=adult_name,
        adult_gender=adult_gender,
        room=room,
        curiosity_object=curiosity,
        surprise_kind=surprise,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story that includes the words "marry", "croak", and "router" and centers on curiosity.',
        f"Tell a gentle story about {f['child'].id} noticing the {f['router'].label}, hearing a croak, and learning a calm bedtime lesson.",
        f"Write a cozy story where a surprising family news moment helps a child learn that the router is not a toy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    curiosity = f["curiosity"]
    surprise = f["surprise"]
    lesson = f["lesson"]
    return [
        QAItem(
            question="What made the child curious?",
            answer=f"The child was curious because {curiosity.prompt.lower()} The blinking router light and the little croak made the child want to know more."
        ),
        QAItem(
            question="What was the surprise?",
            answer=f"The surprise was {surprise.reveal} It changed the bedtime mood into something warm and happy."
        ),
        QAItem(
            question="What lesson did the child learn?",
            answer=f"{lesson.text} {lesson.safe_alternative} The child listened, and the room ended calm instead of noisy."
        ),
        QAItem(
            question="Why was the story bedtime-safe?",
            answer=f"The grown-up stayed gentle, answered questions, and guided the child away from the router. That kept the ending soft, quiet, and ready for sleep."
        ),
        QAItem(
            question="Where did the story end?",
            answer=f"It ended in {f['setting'].label}, with the router blinking calmly and the child drifting toward dreams."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a router?",
            answer="A router is a device that helps messages and internet signals move around a house. It is a grown-up tool, not a toy."
        ),
        QAItem(
            question="What does a croak sound like?",
            answer="A croak is a rough little frog-like sound. It often makes children look around in surprise."
        ),
        QAItem(
            question="What does it mean to marry?",
            answer="To marry means two grown-ups make a promise to share their lives and care for each other. It is a happy grown-up promise."
        ),
    ]


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


ASP_RULES = r"""
curious(ch) :- curiosity(ch), router(rt), notices(ch, rt).
croak_heard(room) :- croak(frog), in_room(frog, room).
lesson_learned(ch) :- adult(a), calm(a), child(ch), guided(a, ch).
valid(room, curiosity, surprise) :- setting(room), curiosity(curiosity), surprise(surprise).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CURIOSITIES:
        lines.append(asp.fact("curiosity", cid))
    for spid in SURPRISES:
        lines.append(asp.fact("surprise", spid))
    lines.append(asp.fact("router", "router"))
    lines.append(asp.fact("croak", "frog"))
    lines.append(asp.fact("marry", "wedding"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH between ASP and Python valid_combos().")
    try:
        sample = generate(resolve_params(argparse.Namespace(room=None, curiosity=None, surprise=None, name=None, adult=None, gender=None, adult_gender=None), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as ex:
        print(f"SMOKE TEST FAILED: {ex}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.room not in SETTINGS:
        raise StoryError("Unknown room.")
    if params.curiosity_object not in CURIOSITIES:
        raise StoryError("Unknown curiosity.")
    if params.surprise_kind not in SURPRISES:
        raise StoryError("Unknown surprise.")
    world = tell(
        SETTINGS[params.room],
        CURIOSITIES[params.curiosity_object],
        SURPRISES[params.surprise_kind],
        LESSONS[params.curiosity_object] if params.curiosity_object in LESSONS else LESSONS["router"],
        child_name=params.child_name,
        child_gender=params.child_gender,
        adult_name=params.adult_name,
        adult_gender=params.adult_gender,
    )
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
        print("== prompts ==")
        for p in sample.prompts:
            print(p)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print("Q:", item.question)
            print("A:", item.answer)
        print("\n== world qa ==")
        for item in sample.world_qa:
            print("Q:", item.question)
            print("A:", item.answer)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("compatible combos:")
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(child_name="Mia", child_gender="girl", adult_name="Mom", adult_gender="woman", room="bedroom", curiosity_object="router", surprise_kind="marry"),
            StoryParams(child_name="Noah", child_gender="boy", adult_name="Dad", adult_gender="man", room="living_room", curiosity_object="frog", surprise_kind="gift"),
            StoryParams(child_name="Ivy", child_gender="girl", adult_name="Aunt June", adult_gender="aunt", room="hallway", curiosity_object="wedding", surprise_kind="note"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen = set()
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
