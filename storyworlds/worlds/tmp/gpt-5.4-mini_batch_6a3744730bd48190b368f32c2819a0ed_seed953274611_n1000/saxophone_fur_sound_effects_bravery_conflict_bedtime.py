#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/saxophone_fur_sound_effects_bravery_conflict_bedtime.py
========================================================================================

A small bedtime-story world about a child, a noisy saxophone, and a soft fur toy.
The story turns on sound effects, bravery, and a gentle conflict that gets resolved
before sleep.

The world model keeps physical meters and emotional memes, and the prose is driven
by simulated events rather than a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

BEDTIME_THRESHOLD = 1.0
BRAVERY_INIT = 4.0
CONFLICT_THRESHOLD = 1.0


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
    tags: set[str] = field(default_factory=set)

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
class Place:
    id: str
    label: str
    quiet: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class SoundThing:
    id: str
    label: str
    phrase: str
    sound: str
    loud: bool = False
    playful: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class FurThing:
    id: str
    label: str
    phrase: str
    soft: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Reaction:
    id: str
    sense: int
    calm: int
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
        import copy as _copy
        clone = World()
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for child in world.entities.values():
        if child.memes["conflict"] < CONFLICT_THRESHOLD:
            continue
        sig = ("conflict", child.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child.memes["worry"] += 1
        out.append("__conflict__")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes["bravery"] < BRAVERY_INIT:
        return out
    sig = ("brave",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["bravery_shine"] += 1
    out.append("__brave__")
    return out


CAUSAL_RULES = [_r_conflict, _r_bravery]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)


def sound_at_risk(sound: SoundThing, place: Place) -> bool:
    return sound.loud and place.quiet


def sensible_reactions() -> list[Reaction]:
    return [r for r in REACTIONS.values() if r.sense >= 2]


def bedtimesafe(place: Place, sound: SoundThing, fur: FurThing) -> bool:
    return sound_at_risk(sound, place) and fur.soft


def predict_world(world: World, sound_id: str) -> dict:
    sim = world.copy()
    _use_sound(sim, sim.get(sound_id), narrate=False)
    return {
        "conflict": sim.get("child").memes["conflict"],
        "worry": sim.get("child").memes["worry"],
    }


def _use_sound(world: World, sound: Entity, narrate: bool = True) -> None:
    child = world.get("child")
    fur = world.get("fur")
    child.meters["noise"] += 1
    child.memes["excitement"] += 1
    if sound.label:
        fur.meters["ruffled"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, child: Entity, parent: Entity, place: Place, fur: FurThing) -> None:
    child.memes["joy"] += 1
    world.say(
        f"At bedtime, {child.id} and {parent.label_word} sat in the quiet little room "
        f"with {fur.phrase} beside the pillow."
    )
    world.say(
        f"The room was so still that even the moonlight seemed to whisper on the wall."
    )


def want_sound(world: World, child: Entity, sound: SoundThing) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"Then {child.id} spotted {sound.phrase}. {child.pronoun().capitalize()} "
        f"wanted to try it, just once."
    )
    world.say(f'"{sound.sound}" went the idea in {child.id}\'s head.')


def warn(world: World, parent: Entity, child: Entity, sound: SoundThing, place: Place) -> None:
    pred = predict_world(world, "sound")
    world.facts["predicted_worry"] = pred["worry"]
    child.memes["conflict"] += 1
    world.say(
        f'{parent.label_word.capitalize()} stroked {child.pronoun("possessive")} hair and said, '
        f'"Not too loud, sweetheart. This room is for resting, and {sound.label} can wake the whole house."'
    )


def defy_or_pause(world: World, child: Entity, parent: Entity, sound: SoundThing) -> None:
    if child.memes["bravery"] >= 5:
        world.say(
            f'{child.id} took a brave breath and said, "But I want to hear how it sounds."'
        )
    else:
        world.say(f"{child.id} looked at the floor and held the {sound.label} quietly.")


def play_sound(world: World, child: Entity, sound: SoundThing, fur: FurThing) -> None:
    _use_sound(world, world.get("sound"))
    world.say(
        f"{sound.sound}! The little saxophone made a bright, bouncy note. "
        f"The {fur.label} on the bed trembled with the tiny tune."
    )
    child.memes["conflict"] += 1


def settle(world: World, parent: Entity, child: Entity, sound: SoundThing, reaction: Reaction) -> None:
    child.meters["noise"] = 0
    child.memes["conflict"] = 0
    child.memes["calm"] += 1
    world.say(
        f"Then {parent.label_word.capitalize()} came closer and {reaction.text}."
    )
    world.say(
        f"The saxophone grew quiet again, and the fur stayed soft and still."
    )


def ending(world: World, child: Entity, parent: Entity, sound: SoundThing, fur: FurThing, reaction: Reaction) -> None:
    world.say(
        f"After that, {child.id} tucked {fur.phrase} under the blanket and listened "
        f"to the room breathe gently."
    )
    world.say(
        f"{child.id} felt brave without making a fuss, and the little saxophone waited "
        f"for morning."
    )


def tell(place: Place, sound: SoundThing, fur: FurThing, reaction: Reaction,
         child_name: str = "Mina", child_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent", role="parent"))
    world.add(Entity(id="sound", type="sound", label=sound.label))
    world.add(Entity(id="fur", type="fur", label=fur.label))

    child.memes["bravery"] = BRAVERY_INIT
    opening(world, child, parent, place, fur)
    world.para()
    want_sound(world, child, sound)
    warn(world, parent, child, sound, place)
    defy_or_pause(world, child, parent, sound)

    if bedtimesafe(place, sound, fur):
        world.para()
        play_sound(world, child, sound, fur)
        settle(world, parent, child, sound, reaction)
    else:
        world.para()
        world.say("But the room liked quiet better, so everyone agreed to wait until morning.")
        world.say("The saxophone rested in its case, and the fur toy kept watch beside the bed.")

    world.para()
    ending(world, child, parent, sound, fur, reaction)
    world.facts.update(
        child=child, parent=parent, place=place, sound=sound, fur=fur,
        reaction=reaction, used=bedtimesafe(place, sound, fur),
        conflict=child.memes["conflict"] >= CONFLICT_THRESHOLD,
        brave=child.memes["bravery"] >= BRAVERY_INIT,
    )
    return world


PLACES = {
    "bedroom": Place(id="bedroom", label="the bedroom", quiet=True, tags={"bedtime"}),
    "nursery": Place(id="nursery", label="the nursery", quiet=True, tags={"bedtime"}),
    "hall": Place(id="hall", label="the hall", quiet=False, tags={"echo"}),
}

SOUNDS = {
    "tiny": SoundThing(id="tiny", label="tiny saxophone", phrase="a tiny saxophone", sound="Toot", loud=False, playful=True, tags={"saxophone"}),
    "bright": SoundThing(id="bright", label="bright saxophone", phrase="a bright saxophone", sound="TOOT!", loud=True, playful=True, tags={"saxophone", "sound_effects"}),
    "mid": SoundThing(id="mid", label="little saxophone", phrase="a little saxophone", sound="Pee-oo!", loud=True, playful=False, tags={"saxophone", "sound_effects"}),
}

FURS = {
    "bear": FurThing(id="bear", label="fur bear", phrase="a fur bear", soft=True, tags={"fur"}),
    "cat": FurThing(id="cat", label="fur cat", phrase="a fur cat", soft=True, tags={"fur"}),
}

REACTIONS = {
    "soft": Reaction(id="soft", sense=3, calm=3, text="helped guide the note into a soft, sleepy whisper", fail="tried to hush it, but the note was too loud", qa_text="helped make the sound soft and sleepy", tags={"calm"}),
    "case": Reaction(id="case", sense=3, calm=2, text="closed the saxophone case and tucked it under the chair", fail="closed the case too late to keep the house asleep", qa_text="closed the saxophone case and put the music away", tags={"calm"}),
    "wait": Reaction(id="wait", sense=2, calm=2, text="asked them to wait until morning and promised a brighter time for music", fail="asked them to wait, but nobody listened", qa_text="asked them to wait until morning", tags={"calm"}),
}

GIRL_NAMES = ["Mina", "Luna", "Nora", "Ivy", "Ella", "Ruby"]
BOY_NAMES = ["Ezra", "Theo", "Finn", "Owen", "Leo", "Milo"]


@dataclass
class StoryParams:
    place: str
    sound: str
    fur: str
    reaction: str
    child_name: str
    child_gender: str
    parent_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for s in SOUNDS:
            for f in FURS:
                if bedtimesafe(PLACES[p], SOUNDS[s], FURS[f]):
                    combos.append((p, s, f))
    return combos


def explain_rejection(place: Place, sound: SoundThing, fur: FurThing) -> str:
    if not place.quiet and sound.loud:
        return "(No story: this hall is too noisy for a bedtime saxophone scene.)"
    if not fur.soft:
        return "(No story: the fur toy must be soft for this bedtime world.)"
    return "(No story: this combination does not make a bedtime conflict.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world with saxophone, fur, bravery, and conflict.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--fur", choices=FURS)
    ap.add_argument("--reaction", choices=REACTIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if args.place and args.sound and args.fur:
        if not bedtimesafe(PLACES[args.place], SOUNDS[args.sound], FURS[args.fur]):
            raise StoryError(explain_rejection(PLACES[args.place], SOUNDS[args.sound], FURS[args.fur]))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.sound is None or c[1] == args.sound)
              and (args.fur is None or c[2] == args.fur)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, sound, fur = rng.choice(sorted(combos))
    reaction = args.reaction or rng.choice(sorted(REACTIONS))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, sound=sound, fur=fur, reaction=reaction,
                       child_name=child_name, child_gender=gender, parent_type=parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a young child that includes the words "{f["sound"].label}" and "{f["fur"].label}".',
        f"Tell a gentle story where {f['child'].id} shows bravery with {f['sound'].phrase}, but there is a small conflict about bedtime quiet.",
        f"Write a child-friendly story in which a parent guides a child from noisy excitement to a calm ending with a fur toy nearby.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, sound, fur, reaction = f["child"], f["parent"], f["sound"], f["fur"], f["reaction"]
    ans1 = (
        f"The story is about {child.id}, {parent.label_word}, and a {fur.label} beside the bed. "
        f"It starts in {f['place'].label} and moves from a noisy idea to a calmer bedtime."
    )
    ans2 = (
        f"{child.id} wanted to try {sound.phrase}, and {parent.label_word} worried it would wake the house. "
        f"That is why the child felt a little conflict before choosing a calmer way."
    )
    ans3 = (
        f"{parent.label_word.capitalize()} {reaction.qa_text}. "
        f"That helped the room stay sleepy and let the fur toy rest quietly."
    )
    return [
        QAItem(question="Who is the story about?", answer=ans1),
        QAItem(question=f"Why was there conflict about the saxophone?", answer=ans2),
        QAItem(question="How did the parent respond?", answer=ans3),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a saxophone?", answer="A saxophone is a musical instrument. People blow into it and press keys to make notes."),
        QAItem(question="Why is fur soft?", answer="Fur is soft because it is made of many fine hairs that lie close together."),
        QAItem(question="Why are bedtime stories calm?", answer="Bedtime stories are calm because they help children feel safe, slow down, and get ready to sleep."),
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        s = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={dict(m)}")
        if s:
            bits.append(f"memes={dict(s)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={dict(e.attrs)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="bedroom", sound="bright", fur="bear", reaction="soft", child_name="Mina", child_gender="girl", parent_type="mother"),
    StoryParams(place="nursery", sound="mid", fur="cat", reaction="wait", child_name="Ezra", child_gender="boy", parent_type="father"),
    StoryParams(place="bedroom", sound="tiny", fur="bear", reaction="case", child_name="Luna", child_gender="girl", parent_type="mother"),
]


def generate(params: StoryParams) -> StorySample:
    for key, table in [("place", PLACES), ("sound", SOUNDS), ("fur", FURS), ("reaction", REACTIONS)]:
        if getattr(params, key) not in table:
            raise StoryError(f"(Invalid {key}: {getattr(params, key)!r}.)")
    world = tell(
        PLACES[params.place],
        SOUNDS[params.sound],
        FURS[params.fur],
        REACTIONS[params.reaction],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent_type,
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
        print(format_qa(sample))


ASP_RULES = r"""
quiet(P) :- place(P), not noisy(P).
bedtime_ok(P,S,F) :- place(P), sound(S), fur(F), quiet(P), loud(S), soft(F).
conflict(C) :- child(C), brave(C), wants_sound(C), parent_warns(C), bedtime_ok(_,_,_).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.quiet:
            lines.append(asp.fact("quiet", pid))
    for sid, s in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        if s.loud:
            lines.append(asp.fact("loud", sid))
    for fid, f in FURS.items():
        lines.append(asp.fact("fur", fid))
        if f.soft:
            lines.append(asp.fact("soft", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show bedtime_ok/3."))
    return sorted(set(asp.atoms(model, "bedtime_ok")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH between ASP and Python valid_combos().")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, qa=True)
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show bedtime_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible bedtime combos:")
        for p, s, f in combos:
            print(f"  {p:8} {s:8} {f}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.child_name}: {p.sound} with {p.fur} ({p.place})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
