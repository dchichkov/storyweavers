#!/usr/bin/env python3
"""
storyworlds/worlds/captivate_tender_complexity_dialogue_rhyme_fable.py
=====================================================================

A small fable-style story world about a young performer, a tender friend, and
the hard lesson that a charming idea can lose a crowd if it becomes too complex.

Seed words:
- captivate
- tender
- complexity

Features:
- Dialogue
- Rhyme

Style:
- Fable

The world is built around a simple stage tale: one character wants to dazzle a
listening crowd with a clever performance; a tender friend warns that too much
complexity will confuse the audience; they argue in dialogue; then they simplify
the act, and the ending proves the lesson with a warm, satisfying image.
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
MORAL_MIN = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "doe"}
        male = {"boy", "father", "dad", "man", "stag", "fox"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Venue:
    id: str
    place: str
    mood: str
    echo: str
    crowd: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Act:
    id: str
    title: str
    rhyme: str
    flourish: str
    steps: int
    complexity: int
    captivates: int
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_confuse(world: World) -> list[str]:
    out: list[str] = []
    performer = world.get("performer")
    if performer.meters["complexity"] >= THRESHOLD and "audience" in world.entities:
        sig = ("confuse", performer.id)
        if sig not in world.fired:
            world.fired.add(sig)
            performer.memes["doubt"] += 1
            world.get("audience").memes["restless"] += 1
            out.append("__confuse__")
    return out


def _r_soothe(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    performer = world.get("performer")
    if helper.memes["tenderness"] >= THRESHOLD and performer.memes["doubt"] >= THRESHOLD:
        sig = ("soothe", helper.id)
        if sig not in world.fired:
            world.fired.add(sig)
            performer.memes["calm"] += 1
            out.append("__soothe__")
    return out


CAUSAL_RULES = [
    Rule("confuse", "social", _r_confuse),
    Rule("soothe", "social", _r_soothe),
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


def act_risk(act: Act) -> bool:
    return act.complexity >= 2


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def is_simple_enough(response: Response, act: Act) -> bool:
    return response.power >= act.complexity


def _do_act(world: World, act: Act, narrate: bool = True) -> None:
    perf = world.get("performer")
    perf.meters["complexity"] += act.complexity
    perf.meters["performance"] += 1
    perf.memes["pride"] += 1
    if act.steps >= 3:
        perf.meters["drama"] += 1
    propagate(world, narrate=narrate)


def predict_audience(world: World, act: Act) -> dict:
    sim = world.copy()
    _do_act(sim, act, narrate=False)
    return {
        "restless": sim.get("audience").memes["restless"],
        "doubt": sim.get("performer").memes["doubt"],
    }


def opening(world: World, venue: Venue, performer: Entity, helper: Entity) -> None:
    world.say(
        f"In {venue.place}, where the air felt {venue.mood} and the candles gave a soft {venue.echo}, "
        f"{performer.id} and {helper.id} prepared for the little crowd."
    )
    world.say(
        f"{performer.id} wanted to {performer.attrs['goal']}, while {helper.id} watched with a {helper.attrs['kind']} and {helper.attrs['heart']} face."
    )


def dialogue_tempt(world: World, performer: Entity, act: Act) -> None:
    world.say(
        f'"I can captivate them," said {performer.id}, "if I weave {act.title} with every twist and turn."'
    )
    world.say(
        f'"That is a shining thought," {world.get("helper").id} replied, "but too much complexity can turn a song into a knot."'
    )


def warning(world: World, helper: Entity, act: Act) -> None:
    helper.memes["tenderness"] += 1
    world.say(
        f'With a tender smile, {helper.id} said, "{act.rhyme} is lovely, but the crowd must be able to follow the tune."'
    )


def choice_back_down(world: World, performer: Entity, helper: Entity, act: Act) -> None:
    performer.memes["pride"] = max(0.0, performer.memes["pride"] - 1.0)
    performer.memes["calm"] += 1
    world.say(
        f'{performer.id} looked at {helper.id}, then nodded. "You are right. A bright pearl can be small, and still be seen."'
    )
    world.say(
        f'Together they pared the act down until it was neat and true, more clear than clever.'
    )


def perform(world: World, act: Act) -> None:
    world.say(
        f'{world.get("performer").id} stepped into the lantern light and began: "{act.rhyme}"'
    )
    _do_act(world, act, narrate=False)
    if world.get("audience").memes["restless"] >= THRESHOLD:
        world.say(
            f"At first the words sparkled, but the more turns they made, the more the little crowd blinked and fidgeted."
        )


def soothe_and_simplify(world: World, response: Response, act: Act) -> None:
    world.say(
        f"{world.get('helper').id} stepped beside the performer and {response.text.replace('{act}', act.title)}."
    )
    world.get("performer").meters["complexity"] = 1.0
    world.get("audience").memes["restless"] = 0.0
    world.get("performer").memes["doubt"] = 0.0


def ending(world: World, venue: Venue, act: Act) -> None:
    perf = world.get("performer")
    helper = world.get("helper")
    world.say(
        f"In the end, the crowd leaned close again, and {venue.crowd} smiled as the shorter song rang bright as a bell."
    )
    world.say(
        f"The fable's lesson was plain: a tender heart can captivate better than a tangled show, and simple words often carry farther than a proud flourish."
    )
    if perf.meters["complexity"] <= 1.0:
        world.say(
            f"{perf.id} and {helper.id} bowed together, one lantern between them, and the night stayed warm and easy."
        )


def tale(venue: Venue, act: Act, response: Response,
         performer_name: str = "Pip", performer_type: str = "fox",
         helper_name: str = "Mira", helper_type: str = "rabbit") -> World:
    world = World()
    performer = world.add(Entity(id=performer_name, kind="character", type=performer_type, role="performer"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type, role="helper"))
    audience = world.add(Entity(id="audience", kind="character", type="crowd", label=venue.crowd))
    world.add(Entity(id="stage", type="thing", label=venue.place))

    performer.attrs["goal"] = "captivate the crowd with a song"
    helper.attrs["kind"] = "tender"
    helper.attrs["heart"] = "gentle"
    performer.memes["hope"] = 1.0
    helper.memes["tenderness"] = 1.0

    opening(world, venue, performer, helper)
    world.para()
    dialogue_tempt(world, performer, act)
    warning(world, helper, act)

    if not act_risk(act):
        choice_back_down(world, performer, helper, act)
        world.para()
        soothe_and_simplify(world, response, act)
        ending(world, venue, act)
        outcome = "simple"
    else:
        world.say(
            f"{performer.id} tried the whole grand design anyway, and the extra turns made the tune wobble."
        )
        perform(world, act)
        if is_simple_enough(response, act):
            world.para()
            soothe_and_simplify(world, response, act)
            ending(world, venue, act)
            outcome = "cleared"
        else:
            world.para()
            world.say(
                f"No gentle fix could hold it then, and the little crowd drifted away before the final rhyme."
            )
            world.say(
                f"The performer learned that captivate is not the same as impress, and complexity can cloud a tender idea."
            )
            outcome = "tangled"

    world.facts.update(
        performer=performer,
        helper=helper,
        audience=audience,
        venue=venue,
        act=act,
        response=response,
        outcome=outcome,
    )
    return world


VENUES = {
    "orchard": Venue("orchard", "the orchard", "golden", "hummed", "apples and birds", tags={"orchard"}),
    "lantern_hall": Venue("lantern_hall", "the lantern hall", "soft", "glowed", "neighbors", tags={"lantern"}),
    "meadow": Venue("meadow", "the meadow", "green", "whispered", "butterflies and bees", tags={"meadow"}),
}

ACTS = {
    "riddle_song": Act("riddle_song", "a riddle-song", "Rhyme a line, then let it shine", "twisting verses", 4, 3, 3, tags={"rhyme"}),
    "little_ballad": Act("little_ballad", "a little ballad", "Soft words float, and gentle hearts note", "clear steps", 2, 1, 2, tags={"rhyme"}),
    "twist_tale": Act("twist_tale", "a twisty tale", "Turn by turn, the bright words burn", "many turns", 5, 4, 4, tags={"rhyme"}),
}

RESPONSES = {
    "simplify": Response("simplify", 3, 4,
                         "simplified the song, cut the extra knots away, and let the rhyme breathe",
                         "could not untie the song in time",
                         "simplified the song"),
    "soften": Response("soften", 2, 3,
                       "softened the words and smoothed the tune until it could be followed",
                       "softened the tune too little to help",
                       "softened the tune"),
}

PERFORMER_NAMES = ["Pip", "Lina", "Moss", "Tavi", "Noor", "Rin"]
HELPER_NAMES = ["Mira", "Sol", "June", "Bram", "Wren", "Nia"]


@dataclass
class StoryParams:
    venue: str
    act: str
    response: str
    performer_name: str
    performer_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "rhyme": [("What is a rhyme?", "A rhyme is when words sound alike at the end, like glow and show. Rhymes can make a song feel playful and easy to remember.")],
    "complexity": [("What does complexity mean?", "Complexity means something has many parts or turns. If a story or song is too complex, it can be hard to follow.")],
    "tender": [("What does tender mean?", "Tender means gentle, careful, and kind. A tender voice is soft and full of care.")],
    "captivate": [("What does captivate mean?", "To captivate is to catch someone's full attention in a pleasing way. A good tale can captivate a room.")],
    "fable": [("What is a fable?", "A fable is a short story that teaches a lesson. Often it ends with a simple moral you can remember.")],
}
KNOWLEDGE_ORDER = ["captivate", "tender", "complexity", "rhyme", "fable"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for v in VENUES:
        for a in ACTS:
            if ACTS[a].complexity >= 1:
                for r in RESPONSES:
                    combos.append((v, a, r))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable for a child that uses the words "captivate", "tender", and "complexity", and includes dialogue and rhyme.',
        f"Tell a small moral story where {f['performer'].id} wants to captivate the crowd with {f['act'].title}, but {f['helper'].id} gently warns that too much complexity will tangle the song.",
        f'Write a rhyme-filled fable set in {f["venue"].place} about a performer and a tender friend choosing a simpler performance.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    performer: Entity = f["performer"]
    helper: Entity = f["helper"]
    act: Act = f["act"]
    venue: Venue = f["venue"]
    response: Response = f["response"]
    out: list[tuple[str, str]] = [
        ("Who are the story's main characters?",
         f"The story is about {performer.id} and {helper.id}. {performer.id} is the one trying to captivate the crowd, and {helper.id} is the tender friend who gives careful advice."),
        ("What did the performer want to do?",
         f"{performer.id} wanted to captivate the crowd with {act.title}. {performer.pronoun().capitalize()} hoped the rhyme would shine like a little star."),
        ("Why did the tender friend warn about the act?",
         f"{helper.id} warned that the act had too much complexity, so the crowd might lose the thread. The warning mattered because the performance had many turns and could easily tangle."),
    ]
    if f["outcome"] == "cleared":
        out.append((
            "How did they solve the problem?",
            f"They simplified the song and let the rhyme breathe again. That made the performance easier to follow, so the crowd could listen all the way through."
        ))
        out.append((
            "How did the story end?",
            f"It ended with a warm, easy bow in {venue.place}. The crowd smiled, and the moral was clear: tender care can captivate better than showy complexity."
        ))
    elif f["outcome"] == "simple":
        out.append((
            "What changed after the warning?",
            f"{performer.id} agreed to keep the performance simple. The smaller rhyme still captivated the crowd, and the story stayed calm and bright."
        ))
    else:
        out.append((
            "What happened when the act stayed too tangled?",
            f"The song grew hard to follow, and the crowd drifted away before the end. The story teaches that captivate works best when complexity does not get in the way."
        ))
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["act"].tags) | {"fable"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("orchard", "riddle_song", "simplify", "Pip", "fox", "Mira", "rabbit"),
    StoryParams("lantern_hall", "twist_tale", "soften", "Lina", "bird", "Sol", "deer"),
    StoryParams("meadow", "little_ballad", "simplify", "Tavi", "mouse", "Nia", "hare"),
]


def outcome_of(params: StoryParams) -> str:
    if ACTS[params.act].complexity <= 1:
        return "simple"
    return "cleared" if RESPONSES[params.response].power >= ACTS[params.act].complexity else "tangled"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for v in VENUES:
        lines.append(asp.fact("venue", v))
    for a in ACTS.values():
        lines.append(asp.fact("act", a.id))
        lines.append(asp.fact("complexity", a.id, a.complexity))
    for r in RESPONSES.values():
        lines.append(asp.fact("response", r.id))
        lines.append(asp.fact("power", r.id, r.power))
        lines.append(asp.fact("sense", r.id, r.sense))
    return "\n".join(lines)


ASP_RULES = r"""
valid(V, A, R) :- venue(V), act(A), response(R), complexity(A, C), power(R, P), C >= 1, P >= 2.
outcome(simple)  :- complexity(A, C), C <= 1.
outcome(cleared) :- complexity(A, C), power(R, P), C > 1, P >= C.
outcome(tangled) :- complexity(A, C), power(R, P), C > 1, P < C.
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen", params.act),
        asp.fact("chosen_response", params.response),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos()")
    cases = list(CURATED)
    rng = random.Random(777)
    for _ in range(20):
        cases.append(resolve_params(build_parser().parse_args([]), rng))
    if all(asp_outcome(p) == outcome_of(p) for p in cases):
        print(f"OK: ASP outcome matches Python on {len(cases)} cases.")
    else:
        rc = 1
        print("MISMATCH in outcome model.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable-like story world about captivate, tender, and complexity.")
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--act", choices=ACTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    combos = [c for c in valid_combos()
              if (args.venue is None or c[0] == args.venue)
              and (args.act is None or c[1] == args.act)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    venue, act, response = rng.choice(sorted(combos))
    return StoryParams(
        venue=venue,
        act=act,
        response=response,
        performer_name=args.name or rng.choice(PERFORMER_NAMES),
        performer_type="fox",
        helper_name=args.helper or rng.choice(HELPER_NAMES),
        helper_type="rabbit",
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tale(
        VENUES[params.venue],
        ACTS[params.act],
        RESPONSES[params.response],
        params.performer_name,
        params.performer_type,
        params.helper_name,
        params.helper_type,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for v, a, r in combos:
            print(f"  {v:12} {a:12} {r}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.performer_name} and {p.helper_name}: {p.act} in {p.venue} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
