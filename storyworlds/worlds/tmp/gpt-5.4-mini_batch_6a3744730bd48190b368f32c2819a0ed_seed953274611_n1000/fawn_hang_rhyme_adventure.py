#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fawn_hang_rhyme_adventure.py
=============================================================

A small standalone storyworld about a young fawn on an adventure, a hanging
problem, and a clever fix. The story is built from simulated state so the
prose changes with the world.

Seed words:
- fawn
- hang

Feature:
- Rhyme

Style:
- Adventure
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
BRAVE_INIT = 4.0


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
        if self.type in {"fawn", "deer"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"mother", "girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"father", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    dark: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    hangable: bool = False
    hanging_risk: bool = False
    safe_light: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    setting: str = "the pine path"
    place: str = "branch"
    hanging: str = "lantern"
    helper: str = "rope"
    rescue: str = "snuffer"
    fawn_name: str = "Fia"
    guide_name: str = "Moss"
    guide_type: str = "fox"
    seed: Optional[int] = None


SETTINGS = {
    "the pine path": Place(id="pine_path", label="the pine path", dark=True, tags={"forest"}),
    "the mossy glade": Place(id="mossy_glade", label="the mossy glade", dark=True, tags={"forest"}),
    "the bright brook": Place(id="bright_brook", label="the bright brook", dark=False, tags={"water"}),
}

HANGINGS = {
    "lantern": Thing(id="lantern", label="lantern", phrase="a little lantern", hangable=True, hanging_risk=True, tags={"light"}),
    "snack_bag": Thing(id="snack_bag", label="snack bag", phrase="a snack bag", hangable=True, hanging_risk=True, tags={"food"}),
    "ribbon": Thing(id="ribbon", label="ribbon", phrase="a bright ribbon", hangable=True, hanging_risk=False, tags={"play"}),
}

HELPERS = {
    "snuffer": Helper(id="snuffer", label="snuffer", sense=3, power=4,
                      text="snuffed the lantern with one quick puff",
                      fail="tried to snuff it, but the sparks were already too lively",
                      qa_text="snuffed the lantern with one quick puff"),
    "blanket": Helper(id="blanket", label="blanket", sense=3, power=3,
                      text="draped a thick blanket over the glow",
                      fail="spread the blanket, but the glow still danced on",
                      qa_text="draped a thick blanket over the glow"),
    "water": Helper(id="water", label="water", sense=1, power=1,
                    text="threw water at the glow",
                    fail="threw water, but it was not enough",
                    qa_text="threw water at the glow"),
}

GIVERS = ["Moss", "Pip", "Rook", "June"]
GUIDES = ["fox", "owl", "squirrel"]
ACTIONS = ["wandered", "ran", "tiptoed", "dashed"]


def hazard_at_risk(setting: Place, hanging: Thing) -> bool:
    return setting.dark and hanging.hanging_risk


def sensible_helpers() -> list[Helper]:
    return [h for h in HELPERS.values() if h.sense >= SENSE_MIN]


def best_helper() -> Helper:
    return max(HELPERS.values(), key=lambda h: h.sense)


def fire_severity(delay: int) -> int:
    return 2 + delay


def is_saved(helper: Helper, delay: int) -> bool:
    return helper.power >= fire_severity(delay)


def _do_hang(world: World, target: Entity) -> None:
    target.meters["sway"] += 1
    target.meters["glow"] += 1


def _spread(world: World) -> None:
    for e in world.entities.values():
        if e.meters["glow"] < THRESHOLD:
            continue
        sig = ("glow_spreads", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("fawn").memes["worry"] += 1
        world.get("guide").memes["alert"] += 1


def predict(world: World, hanging_id: str) -> dict:
    sim = world.copy()
    _do_hang(sim, sim.get(hanging_id))
    _spread(sim)
    return {
        "glowing": sim.get(hanging_id).meters["glow"] >= THRESHOLD,
        "worry": sim.get("fawn").memes["worry"],
    }


def tell_open(world: World, fawn: Entity, guide: Entity, setting: Place) -> None:
    fawn.memes["bravery"] += 1
    world.say(
        f"On {setting.label}, a young fawn named {fawn.id} and {guide.id} went out to explore. "
        f"They wandered where the wind could roam, and each step felt light as foam."
    )
    world.say(
        f'"Look there," said {fawn.id}, with eyes bright and wide, '
        f'"This path feels like an adventure beside!"'
    )


def need_hang(world: World, hanging: Thing) -> None:
    world.say(
        f"But the trees grew tall, and the trail grew long; the shadows were deep, the air felt strong. "
        f"{hanging.phrase} was meant to hang high in sight, so the path could glow and guide the night."
    )


def tempt(world: World, fawn: Entity, hanging: Thing) -> None:
    fawn.memes["curiosity"] += 1
    world.say(
        f'"I know!" said {fawn.id}. "Let us hang {hanging.label} on a low limb near! '
        f"Then we can keep the trail bright and clear.""
    )


def warn(world: World, guide: Entity, fawn: Entity, hanging: Thing, setting: Place) -> None:
    pred = predict(world, "thing")
    guide.memes["caution"] += 1
    world.facts["predicted_worry"] = pred["worry"]
    world.say(
        f"{guide.id} blinked and shook {guide.pronoun('possessive')} head. "
        f'"A low hang can snag and sway; {hanging.label} may fall and dull our way. '
        f"On a dark path, that would be a poor feat; let us choose a safer treat.""
    )


def defy(world: World, fawn: Entity, hanging: Thing) -> None:
    fawn.memes["defiance"] += 1
    world.say(
        f"{fawn.id} still reached up, bold and spry, and tied the {hanging.label} high."
        f" Yet the knot slipped loose with a tiny ping; the path was not the sort of thing."
    )


def hang_it(world: World, target: Entity, hanging: Thing) -> None:
    _do_hang(world, target)
    world.say(
        f"At once the {hanging.label} swung and shone, a little bright bead in the gloam alone. "
        f"But the branch was thin, the placement poor; the lamp tipped down with a trembling roar."
    )


def alarm(world: World, guide: Entity, fawn: Entity) -> None:
    world.say(f'"{fawn.id}!" cried {guide.id}. "The light may drop!"')


def rescue(world: World, guide: Entity, helper: Helper, hanging: Thing) -> None:
    world.get("thing").meters["glow"] = 0.0
    body = helper.text
    world.say(
        f"{guide.id} came quick and {body}. The glow went quiet, the sparks withdrew, "
        f"and the trail was calm and cool and new."
    )
    world.say(
        f"The fawn stood still, then smiled with relief; the adventure was saved from a thorny grief."
    )


def rescue_fail(world: World, guide: Entity, helper: Helper, hanging: Thing) -> None:
    body = helper.fail
    world.say(f"{guide.id} came quick and {body}.")
    world.say(
        "The little light fell to the mossy ground, and the dark went bigger all around."
    )


def lesson(world: World, fawn: Entity, guide: Entity, hanging: Thing) -> None:
    for e in (fawn, guide):
        e.memes["relief"] += 1
        e.memes["lesson"] += 1
    world.say(
        f"{guide.id} smiled and said, \"We tried to roam, but safe light keeps us on the road home. "
        f"Next time we hang it where it belongs, high and steady, where brave hearts sing songs.\""
    )
    world.say(
        f"{fawn.id} nodded at once and tucked in close. The path shone sure, not weak or gross."
    )


def ending_gift(world: World, fawn: Entity, guide: Entity) -> None:
    fawn.memes["joy"] += 1
    guide.memes["joy"] += 1
    world.say(
        f"Then {guide.id} showed {fawn.id} a proper perch, a steady hook near the old tree birch. "
        f"The lantern hung there safe and right, and the whole path gleamed in gentle light."
    )
    world.say(
        f"So the fawn went on, not rushed, not torn; {fawn.id} and {guide.id} were brave by dawn."
    )


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    hanging = HANGINGS[params.hanging]
    helper = HELPERS[params.helper]

    if not hazard_at_risk(setting, hanging):
        raise StoryError("This story needs a dark setting and a hanging object that can fall into trouble.")
    if helper.sense < SENSE_MIN:
        raise StoryError("The chosen rescue is too weak for this adventure.")

    fawn = world.add(Entity(id=params.fawn_name, kind="character", type="fawn", role="hero"))
    guide = world.add(Entity(id=params.guide_name, kind="character", type=params.guide_type, role="guide"))
    thing = world.add(Entity(id="thing", kind="thing", type="thing", label=hanging.label))

    fawn.memes["bravery"] = BRAVE_INIT
    guide.memes["caution"] = 2.0

    tell_open(world, fawn, guide, setting)
    need_hang(world, hanging)
    world.para()
    tempt(world, fawn, hanging)
    warn(world, guide, fawn, hanging, setting)

    if params.setting == "the bright brook":
        world.say("But the brook was bright, and the worry did not bite; they chose another path that felt more right.")
        ending_gift(world, fawn, guide)
        outcome = "averted"
    else:
        defy(world, fawn, hanging)
        world.para()
        hang_it(world, thing, hanging)
        alarm(world, guide, fawn)
        if is_saved(helper, 0):
            world.para()
            rescue(world, guide, helper, hanging)
            lesson(world, fawn, guide, hanging)
            world.para()
            ending_gift(world, fawn, guide)
            outcome = "saved"
        else:
            world.para()
            rescue_fail(world, guide, helper, hanging)
            lesson(world, fawn, guide, hanging)
            outcome = "lost"

    world.facts.update(
        setting=setting,
        hanging=hanging,
        helper=helper,
        fawn=fawn,
        guide=guide,
        outcome=outcome,
        safe=outcome in {"saved", "averted"},
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a young child that includes the words "{f["fawn"].id.lower()}" and "hang".',
        f"Tell a rhyming story where {f['fawn'].id} wants to hang a light for a dark trail, but a guide helps choose the safer way.",
        f"Write a gentle adventure with a fawn, a hanging lantern, and a calm ending that rhymes a little.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    fawn = f["fawn"]
    guide = f["guide"]
    hanging = f["hanging"]
    setting = f["setting"]
    out = f["outcome"]
    qa = [
        ("Who is the story about?",
         f"It is about a young fawn named {fawn.id} and a guide named {guide.id}. They explore {setting.label} together, so the adventure feels small but brave."),
        ("What did the fawn want to do?",
         f"{fawn.id} wanted to hang the {hanging.label} where the trail could shine. The idea sounded clever, but it also made the guide worry."),
    ]
    if out == "saved":
        qa.append((
            "How was the problem solved?",
            f"{guide.id} used the {f['helper'].label} to make the light safe again. That quick fix stopped the trouble, and the path became bright in a steady way."
        ))
    elif out == "averted":
        qa.append((
            "What happened instead of danger?",
            f"They chose not to hang the risky light at all. That kept the adventure calm, and they found a safer way to continue."
        ))
    else:
        qa.append((
            "What happened when the help was too weak?",
            f"The help could not beat the problem, so the glow fell away and the path stayed dark. Even then, the guide and fawn stayed together and learned to be more careful."
        ))
    qa.append((
        "How did the story end?",
        f"It ended with {fawn.id} and {guide.id} continuing the adventure after the trouble passed. The final image is a safer trail and a fawn who has learned to choose a steadier hang."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["hanging"].tags) | {f["setting"].id}
    if f["outcome"] == "saved":
        tags |= set(f["helper"].tags)
    out = []
    for tag, pair in KNOWLEDGE.items():
        if tag in tags:
            out.extend(pair)
    return out


KNOWLEDGE = {
    "light": [("What does a lantern do?",
               "A lantern gives off light so people can see in the dark. It helps a path feel less scary.")],
    "forest": [("What is a forest?",
                "A forest is a place with many trees, plants, and animals. It can feel quiet, shady, and full of hiding spots.")],
    "snuffer": [("What does a snuffer do?",
                 "A snuffer helps put out a small light by stopping the flame or glow safely.")],
    "rope": [("What is a rope for?",
              "A rope can help tie things up or hold them steady. It is useful when something needs to hang in one place.")],
}


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
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="the pine path", place="branch", hanging="lantern", helper="snuffer", rescue="snuffer", fawn_name="Fia", guide_name="Moss", guide_type="fox"),
    StoryParams(setting="the mossy glade", place="branch", hanging="snack_bag", helper="blanket", rescue="blanket", fawn_name="Pip", guide_name="Rue", guide_type="owl"),
    StoryParams(setting="the bright brook", place="branch", hanging="ribbon", helper="snuffer", rescue="snuffer", fawn_name="Nia", guide_name="Tuck", guide_type="squirrel"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s_id, setting in SETTINGS.items():
        for h_id, hanging in HANGINGS.items():
            if not hazard_at_risk(setting, hanging):
                continue
            for helper_id, helper in HELPERS.items():
                if helper.sense >= SENSE_MIN:
                    combos.append((s_id, h_id, helper_id))
    return combos


def explain_rejection(setting: Place, hanging: Thing, helper: Helper) -> str:
    if not hazard_at_risk(setting, hanging):
        return "(No story: the setting is not dark enough for this hanging trouble."
    if helper.sense < SENSE_MIN:
        return "(No story: that rescue is too weak to feel like a real adventure.)"
    return "(No story: this combination does not make a reasonable tale.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small rhyming adventure about a fawn and a hanging light.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hanging", choices=HANGINGS)
    ap.add_argument("--helper", choices=HELPERS)
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
              and (args.hanging is None or c[1] == args.hanging)
              and (args.helper is None or c[2] == args.helper)]
    if args.setting and args.hanging and args.helper:
        if not combos:
            raise StoryError(explain_rejection(SETTINGS[args.setting], HANGINGS[args.hanging], HELPERS[args.helper]))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    s_id, h_id, helper_id = rng.choice(sorted(combos))
    return StoryParams(
        setting=s_id,
        place="branch",
        hanging=h_id,
        helper=helper_id,
        rescue=helper_id,
        fawn_name=rng.choice(["Fia", "Nell", "Bram", "Tavi"]),
        guide_name=rng.choice(["Moss", "Rue", "Tuck", "Pip"]),
        guide_type=rng.choice(["fox", "owl", "squirrel"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.hanging not in HANGINGS or params.helper not in HELPERS:
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
valid(S,H,L) :- setting(S), hanging(H), helper(L), dark(S), risky(H), sense(L,SN), sense_min(M), SN >= M.
saved(L,D) :- helper(L), power(L,P), severity(D,V), P >= V.
severity(D, V) :- delay(D), V = 2 + D.
outcome(averted) :- setting("the bright brook").
outcome(saved) :- not outcome(averted), saved(L,0).
outcome(lost) :- not outcome(averted), not saved(L,0).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.dark:
            lines.append(asp.fact("dark", sid))
    for hid, h in HANGINGS.items():
        lines.append(asp.fact("hanging", hid))
        if h.hanging_risk:
            lines.append(asp.fact("risky", hid))
    for lid, l in HELPERS.items():
        lines.append(asp.fact("helper", lid))
        lines.append(asp.fact("sense", lid, l.sense))
        lines.append(asp.fact("power", lid, l.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("delay", 0))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid-combos differ.")
        rc = 1
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            sample = generate(CURATED[0])
            emit(sample)
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < 100:
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
