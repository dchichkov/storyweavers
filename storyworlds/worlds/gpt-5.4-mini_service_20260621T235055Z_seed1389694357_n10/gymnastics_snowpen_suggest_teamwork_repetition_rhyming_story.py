#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260621T235055Z_seed1389694357_n10/gymnastics_snowpen_suggest_teamwork_repetition_rhyming_story.py
===============================================================================================================================

A tiny storyworld about two children, a snowy pen, and a cheerful teamwork plan.

Premise:
- Two young gymnasts play in a snowpen, a round snowy practice space.
- One child wants to show off; the other suggests teamwork and repetition.
- They repeat a simple rhythm, help each other through a small wobble, and finish in a bright, rhyming pose.

The world is deliberately small and classical:
- typed entities with physical meters and emotional memes
- a causal rule engine
- a Python reasonableness gate
- an inline ASP twin
- three QA sets grounded in world state

The story text is child-facing and rhyming, but it still follows a clear
beginning, turn, and ending image that proves what changed.
"""

from __future__ import annotations

import argparse
import copy
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

# Robust bootstrap: walk upward until we find storyworlds/results.py.
_HERE = Path(__file__).resolve()
for _parent in [_HERE.parent, *_HERE.parents]:
    if (_parent / "results.py").exists():
        sys.path.insert(0, str(_parent))
        break
else:  # pragma: no cover
    raise RuntimeError("Could not locate storyworlds/results.py")

from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2

TEAMWORK_TRAITS = {"kind", "steady", "helpful", "patient", "careful"}
RHYME_ENDINGS = {
    "bright": "light",
    "snow": "glow",
    "hold": "gold",
    "near": "cheer",
    "beam": "dream",
}


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


@dataclass
class Place:
    id: str
    label: str
    surface: str
    texture: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    label: str
    repeated_step: str
    wobble: str
    finish: str
    mess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Suggestion:
    id: str
    phrase: str
    effect: str
    teamwork: bool
    repetition: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    comfort: str
    skill: str
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
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_help(world: World) -> list[str]:
    out: list[str] = []
    gymnast = world.get("gymnast1")
    partner = world.get("gymnast2")
    if gymnast.memes["teamwork"] >= THRESHOLD and partner.memes["teamwork"] >= THRESHOLD:
        sig = ("help",)
        if sig not in world.fired:
            world.fired.add(sig)
            gymnast.memes["joy"] += 0.5
            partner.memes["joy"] += 0.5
            out.append("__help__")
    return out


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    if world.get("ramp").meters["slippery"] >= THRESHOLD and ("wobble",) not in world.fired:
        world.fired.add(("wobble",))
        world.get("gymnast1").meters["wobble"] += 1
        world.get("gymnast2").meters["alert"] += 1
        out.append("__wobble__")
    return out


CAUSAL_RULES = [Rule("wobble", _r_wobble), Rule("help", _r_help)]


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


def reasonableness_gate(place: Place, activity: Activity, suggestion: Suggestion) -> bool:
    return (
        "snow" in place.tags
        and activity.id in activity.tags
        and suggestion.teamwork
        and suggestion.repetition
    )


def supports_repetition(activity: Activity) -> bool:
    return activity.id in {"balance", "beam", "spin", "jump"}


def predict_outcome(world: World) -> dict:
    sim = world.copy()
    simulate_motion(sim, narrate=False)
    return {
        "wobble": sim.get("gymnast1").meters["wobble"] >= THRESHOLD,
        "help": sim.get("gymnast1").memes["joy"] > 0,
    }


def simulate_motion(world: World, narrate: bool = True) -> None:
    world.get("gymnast1").meters["flow"] += 1
    world.get("gymnast2").meters["flow"] += 1
    world.get("ramp").meters["slippery"] += 1
    propagate(world, narrate=narrate)


def build_story_line(step: str, rhyme: str) -> str:
    return f"{step}, so their little practice sparkled like {rhyme}."


def tell(place: Place, activity: Activity, suggestion: Suggestion, helper: Helper,
         name1: str = "Mia", name2: str = "Noah") -> World:
    world = World()
    g1 = world.add(Entity(id="gymnast1", kind="character", type="girl", label=name1,
                          role="leader", traits=["bold"], attrs={"partner": name2}))
    g2 = world.add(Entity(id="gymnast2", kind="character", type="boy", label=name2,
                          role="helper", traits=["kind"], attrs={"partner": name1}))
    ramp = world.add(Entity(id="ramp", kind="thing", type="surface", label=place.label,
                            attrs={"texture": place.texture}, tags=set(place.tags)))

    g1.memes["bravery"] = 1
    g2.memes["teamwork"] = 1
    g1.memes["teamwork"] = 1
    g2.memes["joy"] = 0
    g1.memes["joy"] = 0
    ramp.meters["slippery"] = 0
    world.facts["helper"] = helper
    world.facts["place"] = place
    world.facts["activity"] = activity
    world.facts["suggestion"] = suggestion

    world.say(
        f"In the snowpen white, {name1} and {name2} came to play, "
        f"with boots that squeaked and cheeks so bright they seemed to say."
    )
    world.say(
        f"They loved {activity.label}, neat and sweet, with a rhythm small and spry, "
        f"and {name1} planned a daring turn to leap up toward the sky."
    )
    world.para()
    world.say(
        f"{name2} smiled and spoke a friendly word: \"{suggestion.phrase},\" "
        f"{helper.comfort} in the air."
    )
    world.say(
        f"They practiced the same step twice, then twice again, with steady care."
    )
    simulate_motion(world, narrate=False)
    pred = predict_outcome(world)
    world.facts["pred"] = pred

    if pred["wobble"]:
        world.say(
            f"But ice-kiss {place.label} had a little slip, a shiny, sneaky gleam; "
            f"{name1} tipped, then {name2} hopped close by to keep the rhythm's beam."
        )
        world.say(
            f"{name2} took the hand and counted soft: \"One, two, one, two, three!\" "
            f"And {name1} matched the beat, then both moved on so lightly."
        )
    else:
        world.say(
            f"The snowpen held them firm and fine; no wobble dared appear, "
            f"so their two-step teamwork kept the tune as clear as clear can clear."
        )

    world.para()
    world.say(
        f"They tried the {activity.repeated_step} again and again, a tidy, twinkling chain; "
        f"the same small move, the same kind grin, then once more in the lane."
    )
    world.say(
        f"At last they reached the {activity.finish}, hand in hand, and stood up tall and bright, "
        f"with {helper.label} smiling at the edge, like morning after night."
    )

    g1.memes["joy"] += 1
    g2.memes["joy"] += 1
    g1.memes["teamwork"] += 1
    g2.memes["teamwork"] += 1
    world.facts.update(
        gymnast1=g1,
        gymnast2=g2,
        ramp=ramp,
        place=place,
        activity=activity,
        suggestion=suggestion,
        outcome="wobble" if pred["wobble"] else "smooth",
    )
    return world


PLACES = {
    "snowpen": Place(
        id="snowpen",
        label="snowpen",
        surface="snowpen",
        texture="snowy",
        tags={"snow", "pen"},
    ),
    "hillpen": Place(
        id="hillpen",
        label="hillpen",
        surface="hillpen",
        texture="icy",
        tags={"snow", "pen", "ice"},
    ),
    "yardpen": Place(
        id="yardpen",
        label="yardpen",
        surface="yardpen",
        texture="frosty",
        tags={"snow", "pen", "yard"},
    ),
}

ACTIONS = {
    "balance": Activity(
        id="balance",
        label="balance beam steps",
        repeated_step="step, step, stop",
        wobble="wobble",
        finish="starry finish",
        mess="snow dust",
        tags={"gymnastics", "repetition"},
    ),
    "spin": Activity(
        id="spin",
        label="twirl turns",
        repeated_step="turn, turn, grin",
        wobble="wobble",
        finish="sparkling pose",
        mess="snow dust",
        tags={"gymnastics", "repetition"},
    ),
    "jump": Activity(
        id="jump",
        label="jump hops",
        repeated_step="hop, hop, stop",
        wobble="wobble",
        finish="bright landing",
        mess="snow dust",
        tags={"gymnastics", "repetition"},
    ),
}

SUGGESTIONS = {
    "counting": Suggestion(
        id="counting",
        phrase="Let's count it out and do it together",
        effect="counted together",
        teamwork=True,
        repetition=True,
        tags={"teamwork", "repetition", "suggest"},
    ),
    "echo": Suggestion(
        id="echo",
        phrase="You do one, I do one, and then we repeat",
        effect="echoed each move",
        teamwork=True,
        repetition=True,
        tags={"teamwork", "repetition", "suggest"},
    ),
    "pair": Suggestion(
        id="pair",
        phrase="We can pair up and try the step again",
        effect="paired up",
        teamwork=True,
        repetition=True,
        tags={"teamwork", "repetition", "suggest"},
    ),
}

HELPERS = {
    "coach": Helper(id="coach", label="Coach Dot", comfort="a warm nod", skill="steady", tags={"coach"}),
    "friend": Helper(id="friend", label="Pip", comfort="a happy clap", skill="kind", tags={"friend"}),
    "sibling": Helper(id="sibling", label="Big Sis Ray", comfort="a sure smile", skill="helpful", tags={"sibling"}),
}


@dataclass
class StoryParams:
    place: str
    activity: str
    suggestion: str
    helper: str
    gymnast1: str
    gymnast2: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="snowpen", activity="balance", suggestion="counting", helper="coach", gymnast1="Mia", gymnast2="Noah"),
    StoryParams(place="hillpen", activity="spin", suggestion="echo", helper="friend", gymnast1="Lena", gymnast2="Theo"),
    StoryParams(place="yardpen", activity="jump", suggestion="pair", helper="sibling", gymnast1="Ava", gymnast2="Ben"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid in PLACES:
        for aid in ACTIONS:
            for sid in SUGGESTIONS:
                if reasonableness_gate(PLACES[pid], ACTIONS[aid], SUGGESTIONS[sid]):
                    combos.append((pid, aid, sid))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story with the words "gymnastics", "snowpen", and "suggest" about teamwork.',
        f"Tell a child-friendly rhyming tale where {f['gymnast1'].label} and {f['gymnast2'].label} do gymnastics in a snowpen and suggest a teamwork plan.",
        f"Write a short story that repeats a small move, uses the word snowpen, and ends with the children helping each other.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    g1, g2 = f["gymnast1"], f["gymnast2"]
    act, sug, place, helper = f["activity"], f["suggestion"], f["place"], f["helper"]
    qa = [
        QAItem(
            question=f"What did {g1.label} and {g2.label} do in the {place.label}?",
            answer=f"They did {act.label} in the {place.label}. They kept the moves small and repeated them so the practice stayed smooth.",
        ),
        QAItem(
            question=f"Who suggested a teamwork plan?",
            answer=f"{g2.label} suggested it, and {helper.label} helped make the plan feel calm and kind. The suggestion also kept the children repeating the same step together.",
        ),
        QAItem(
            question=f"Why did the children keep repeating the move?",
            answer=f"They repeated the move because {sug.phrase.lower()} and the rhythm helped them stay steady. Repetition made the gymnastics easier to share.",
        ),
    ]
    if f["outcome"] == "wobble":
        qa.append(QAItem(
            question=f"What almost went wrong in the {place.label}?",
            answer=f"The slippery {place.label} made {g1.label} wobble for a moment. {g2.label} moved close, and teamwork turned the wobble into a safe recovery.",
        ))
        qa.append(QAItem(
            question=f"How did the friends fix the wobble?",
            answer=f"They counted together, held hands, and repeated the step again until it felt steady. That teamwork kept the practice going.",
        ))
    else:
        qa.append(QAItem(
            question=f"Did anything stop the practice in the {place.label}?",
            answer=f"No. The {place.label} stayed firm enough, so the children could repeat the move and finish with a bright pose.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags) | set(world.facts["suggestion"].tags) | {"snow", "teamwork", "repetition"}
    out: list[QAItem] = []
    if "gymnastics" in tags:
        out.append(QAItem(
            question="What is gymnastics?",
            answer="Gymnastics is a sport where children move, balance, jump, and turn their bodies in careful and strong ways.",
        ))
    if "snow" in tags:
        out.append(QAItem(
            question="What is a snowpen?",
            answer="A snowpen is a small snowy place or practice area where the snow makes the play feel chilly and bright.",
        ))
    if "teamwork" in tags:
        out.append(QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and do the job together. It can make hard things feel easier.",
        ))
    if "repetition" in tags:
        out.append(QAItem(
            question="Why can repetition help?",
            answer="Repetition means doing the same move again. That can help a child remember it and feel steadier.",
        ))
    if "suggest" in tags:
        out.append(QAItem(
            question="What does it mean to suggest something?",
            answer="To suggest something means to offer an idea in a friendly way. It helps other people think about a good plan.",
        ))
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
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.tags:
            parts.append(f"tags={sorted(e.tags)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
place_ok(P) :- place(P), snow_place(P).
safe_combo(P,A,S) :- place_ok(P), activity(A), suggestion(S), teamwork(S), repetition(S).
wobble_possible(A) :- activity(A), repeats(A).
outcome(wobble) :- chosen(P,A,S), safe_combo(P,A,S), wobble_possible(A).
outcome(smooth) :- chosen(P,A,S), safe_combo(P,A,S), not wobble_possible(A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if "snow" in p.tags:
            lines.append(asp.fact("snow_place", pid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("repeats", aid))
    for sid, s in SUGGESTIONS.items():
        lines.append(asp.fact("suggestion", sid))
        if s.teamwork:
            lines.append(asp.fact("teamwork", sid))
        if s.repetition:
            lines.append(asp.fact("repetition", sid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show safe_combo/3."))
    return sorted(set(asp.atoms(model, "safe_combo")))


def asp_verify() -> int:
    import asp
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        print("  only python:", sorted(py - cl))
        print("  only asp:", sorted(cl - py))
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: smoke test generate() produced a story.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming storyworld about gymnastics in a snowpen.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIONS)
    ap.add_argument("--suggestion", choices=SUGGESTIONS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
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
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.suggestion is None or c[2] == args.suggestion)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, suggestion = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    name1 = args.name1 or rng.choice(["Mia", "Lena", "Ava", "Ivy", "Zoe"])
    name2 = args.name2 or rng.choice(["Noah", "Theo", "Eli", "Owen", "Finn"])
    if name1 == name2:
        name2 = "Noah" if name1 != "Noah" else "Theo"
    return StoryParams(place=place, activity=activity, suggestion=suggestion, helper=helper, gymnast1=name1, gymnast2=name2)


def generate(params: StoryParams) -> StorySample:
    for field_name, table in [("place", PLACES), ("activity", ACTIONS), ("suggestion", SUGGESTIONS), ("helper", HELPERS)]:
        if getattr(params, field_name) not in table:
            raise StoryError(f"Invalid {field_name}: {getattr(params, field_name)}")
    world = tell(PLACES[params.place], ACTIONS[params.activity], SUGGESTIONS[params.suggestion], HELPERS[params.helper], params.gymnast1, params.gymnast2)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(show="#show safe_combo/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} safe combos:\n")
        for c in combos:
            print("  ", c)
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
