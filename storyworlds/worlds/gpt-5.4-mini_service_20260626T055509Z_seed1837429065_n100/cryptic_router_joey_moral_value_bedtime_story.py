#!/usr/bin/env python3
"""
A tiny bedtime-story world about Joey, a cryptic router, and a gentle moral value:
being honest helps everyone find their way home.

The world has one small household domain:
- Joey is a child who likes tapping messages into a little router.
- The router can sort notes to a lamp, a doorbell, or a bedtime star.
- A cryptic note may confuse the route until Joey chooses to be honest and clear.
- The moral value is that clear words and truthful choices make things kinder.

The story is generated from a simulated state, not from a frozen paragraph.
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
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def get(self, key: str, default: float = 0.0) -> float:
        return self.meters.get(key, self.memes.get(key, default))

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "child":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    note: str
    target: str
    mood: str
    seed: Optional[int] = None


PLACES = {
    "hallway": "the hallway",
    "kitchen": "the kitchen",
    "bedroom": "the bedroom",
    "porch": "the porch",
}

TARGETS = {
    "lamp": "a sleepy lamp",
    "doorbell": "the front doorbell",
    "star": "a small bedtime star hanging above the bed",
}

NOTES = {
    "cryptic": "a cryptic note with curled letters and a hidden meaning",
    "clear": "a clear note that said exactly what it meant",
    "sorry": "a sorry note with a soft little heart drawn at the end",
}

MOODS = ["curious", "sleepy", "brave", "gentle"]


# ---------------------------------------------------------------------------
# Simulation helpers
# ---------------------------------------------------------------------------

def setup_world(params: StoryParams) -> World:
    w = World()
    joey = w.add(Entity(
        id="Joey",
        kind="child",
        label="Joey",
        meters={"tiredness": 0.2},
        memes={"curiosity": 1.0, "honesty": 0.0, "worry": 0.0, "peace": 0.0, "pride": 0.0},
    ))
    router = w.add(Entity(
        id="router",
        label="little router",
        phrase="a little router with a blinking blue light",
        meters={"signal": 1.0, "confusion": 0.0},
        memes={"care": 0.0},
    ))
    target = w.add(Entity(
        id=params.target,
        label=TARGETS[params.target],
        phrase=TARGETS[params.target],
        meters={"listening": 1.0},
    ))
    note = w.add(Entity(
        id="note",
        label=NOTES[params.note],
        phrase=NOTES[params.note],
        meters={"clarity": 0.2 if params.note == "cryptic" else 1.0},
        memes={"mystery": 1.0 if params.note == "cryptic" else 0.0},
    ))
    w.facts.update(params=params, joey=joey, router=router, target=target, note=note)
    return w


def propagate(w: World, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        joey = w.get("Joey")
        router = w.get("router")
        note = w.get("note")
        target = w.get(w.facts["params"].target)

        # Cryptic note confuses the router.
        if note.meters.get("clarity", 0.0) < 0.5 and ("cryptic",) not in w.fired:
            w.fired.add(("cryptic",))
            router.meters["confusion"] = router.meters.get("confusion", 0.0) + 1.0
            joey.memes["worry"] += 1.0
            if narrate:
                w.say("The little router blinked and blinked, as if the note were a tiny maze.")

            changed = True

        # Honest clarity calms everything.
        if note.meters.get("clarity", 0.0) >= 0.8 and ("clear",) not in w.fired:
            w.fired.add(("clear",))
            router.meters["confusion"] = 0.0
            joey.memes["peace"] += 1.0
            if narrate:
                w.say("The blinking light softened, because the message could finally be understood.")
            changed = True

        # If Joey is honest, the router routes the note to the right place.
        if joey.memes.get("honesty", 0.0) >= 1.0 and router.meters.get("confusion", 0.0) < 0.5:
            sig = ("routed", w.facts["params"].target)
            if sig not in w.fired:
                w.fired.add(sig)
                target.meters["received"] = 1.0
                if narrate:
                    w.say(f"The router sent the note where it belonged, to {target.label}.")
                changed = True

        # Late honesty removes worry.
        if joey.memes.get("honesty", 0.0) >= 1.0 and joey.memes.get("worry", 0.0) > 0.0:
            sig = ("settle",)
            if sig not in w.fired:
                w.fired.add(sig)
                joey.memes["worry"] = 0.0
                if narrate:
                    w.say("Joey's chest felt lighter, because telling the truth made the room feel kind.")
                changed = True


def predict_outcome(w: World, honest: bool) -> dict:
    sim = w.copy()
    joey = sim.get("Joey")
    note = sim.get("note")
    if honest:
        joey.memes["honesty"] = 1.0
        note.meters["clarity"] = 1.0
    propagate(sim, narrate=False)
    target = sim.get(sim.facts["params"].target)
    return {
        "received": target.meters.get("received", 0.0) >= 1.0,
        "confusion": sim.get("router").meters.get("confusion", 0.0),
        "worry": joey.memes.get("worry", 0.0),
    }


# ---------------------------------------------------------------------------
# Storytelling
# ---------------------------------------------------------------------------

def tell(params: StoryParams) -> World:
    w = setup_world(params)
    joey = w.get("Joey")
    router = w.get("router")
    note = w.get("note")
    target = w.get(params.target)

    w.say(f"At {PLACES[params.place]}, Joey was a {params.mood} little boy who liked the soft blink of the router.")
    w.say(f"He found {note.label} tucked beside the router, and it looked mysterious enough to make him pause.")
    w.say(f"Joey whispered, \"I want to send this note, but I don't know if it says the right thing.\"")

    w.para()
    w.say(f"The router hummed in the quiet room, waiting to carry the message to {target.label}.")
    if params.note == "cryptic":
        w.say("But the note was so cryptic that the blinking light only wobbled in confusion.")
    else:
        w.say("The note was already plain and gentle, so the router had nothing to puzzle over.")

    w.para()
    if params.note == "cryptic":
        w.say("Joey thought about hiding the truth, but he did not like the shaky feeling in his tummy.")
        joey.memes["honesty"] = 1.0
        note.meters["clarity"] = 1.0
        w.say("So he read the note again and said it clearly, in his own simple words.")
    else:
        joey.memes["honesty"] = 1.0
        w.say("Joey smiled and spoke the message out loud, because it was already honest and kind.")

    propagate(w, narrate=True)

    if target.meters.get("received", 0.0) >= 1.0:
        w.say(f"In the end, {target.label} glowed as if it had heard a good bedtime secret.")
        w.say("Joey yawned, and the room felt calm, because the truest words had found their way.")
    else:
        w.say("In the end, the note still waited quietly, and Joey knew he needed a clearer voice tomorrow.")

    return w


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write a bedtime story about Joey, a {p.mood} child, and a {p.note} note that a small router must send.',
        f"Tell a gentle story where Joey learns that being honest helps a router understand a message.",
        f'Write a short bedtime tale that includes a router, a cryptic note, and a moral value about truthfulness.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    note = world.get("note")
    target = world.get(p.target)
    joey = world.get("Joey")
    router = world.get("router")
    return [
        QAItem(
            question="Who is the story about?",
            answer="The story is about Joey, a little boy who meets a tiny router and learns how to send a note kindly.",
        ),
        QAItem(
            question="Why did the router get confused?",
            answer="The router got confused because the note was cryptic and did not say its meaning plainly.",
        ),
        QAItem(
            question="What helped the note travel to the right place?",
            answer="Joey chose to be honest and made the message clear, which let the router send it to the right target.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer="By the end, the confusion was gone, Joey felt peaceful, and the note reached its home.",
        ),
        QAItem(
            question=f"Where did the router send the note in the {p.place} story?",
            answer=f"It sent the note to {target.label}, after Joey turned the message into something clear enough to understand.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a router for?",
            answer="A router helps send messages or signals to the right place so they can arrive where they belong.",
        ),
        QAItem(
            question="What does it mean to be honest?",
            answer="Being honest means telling the truth and saying things clearly instead of hiding or twisting them.",
        ),
        QAItem(
            question="Why can a cryptic note be hard to understand?",
            answer="A cryptic note can be hard to understand because it is puzzling and does not explain itself in a simple way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    out.extend(f"- {p}" for p in sample.prompts)
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
router_confused :- cryptic_note.
clear_message :- clear_note.
received(Target) :- honest, clear_message, target(Target), router_ready.
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("child", "joey"),
        asp.fact("router_ready"),
    ]
    for place in PLACES:
        lines.append(asp.fact("place", place))
    for target in TARGETS:
        lines.append(asp.fact("target", target))
    for note in NOTES:
        if note == "cryptic":
            lines.append(asp.fact("cryptic_note"))
        if note == "clear":
            lines.append(asp.fact("clear_note"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show router_confused/0.\n#show clear_message/0.\n#show received/1.\n{show}\n"


def asp_validate() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program(""))
    out = []
    out.extend(("router_confused", "") for _ in asp.atoms(model, "router_confused"))
    out.extend(("clear_message", "") for _ in asp.atoms(model, "clear_message"))
    out.extend(("received", str(t[0])) for t in asp.atoms(model, "received"))
    return out


def python_gate(params: StoryParams) -> tuple[bool, bool]:
    cryptic = params.note == "cryptic"
    clear = params.note == "clear"
    return cryptic, clear


def asp_verify() -> int:
    import asp
    py_cryptic, py_clear = python_gate(StoryParams(place="hallway", note="cryptic", target="lamp", mood="curious"))
    model = asp.one_model(asp_program(""))
    asp_cryptic = bool(asp.atoms(model, "router_confused"))
    asp_clear = bool(asp.atoms(model, "clear_message"))
    if py_cryptic != asp_cryptic or py_clear != asp_clear:
        print("MISMATCH between Python and ASP gates.")
        print("python:", py_cryptic, py_clear)
        print("asp:", asp_cryptic, asp_clear)
        return 1
    sample = generate(StoryParams(place="hallway", note="cryptic", target="lamp", mood="curious"))
    if not sample.story.strip():
        print("Story generation failed.")
        return 1
    print("OK: ASP/Python parity and story generation verified.")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime-story world about Joey and a cryptic router.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--note", choices=NOTES.keys())
    ap.add_argument("--target", choices=TARGETS.keys())
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES.keys()))
    note = args.note or rng.choice(list(NOTES.keys()))
    target = args.target or rng.choice(list(TARGETS.keys()))
    mood = args.mood or rng.choice(MOODS)
    if note == "cryptic" and target == "doorbell" and args.place is None:
        pass
    return StoryParams(place=place, note=note, target=target, mood=mood)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print()
        print("--- world trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: meters={e.meters} memes={e.memes}")
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="hallway", note="cryptic", target="lamp", mood="curious"),
    StoryParams(place="kitchen", note="clear", target="doorbell", mood="gentle"),
    StoryParams(place="bedroom", note="sorry", target="star", mood="sleepy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(""))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program(""))
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
