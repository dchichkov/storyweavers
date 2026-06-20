#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/nun_phony_genetic_foreshadowing_inner_monologue_adventure.py
=============================================================================================

A standalone storyworld in a tiny adventure domain: a child explorer and a nun
search an old cloister garden for a lost key, a fake clue, and a real science
note about genetic traits in seed packets. The story uses foreshadowing and
inner monologue to build a child-facing adventure with a clear turn and a safe,
resolved ending.

The world is intentionally small and state-driven:
- physical meters track things like clue certainty, danger, and progress
- emotional memes track trust, worry, bravado, and relief
- causal rules advance the simulation to a fixpoint
- the renderer turns the world state into complete prose rather than swapping
  nouns into a frozen paragraph

The required seed words are used in-domain:
- nun
- phony
- genetic

Style: adventure, with foreshadowing and inner monologue.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
        female = {"girl", "mother", "mom", "woman", "nun", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"nun": "sister"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    shadowy: bool = False
    elev: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    kind: str  # phony | real
    story_hint: str
    truth_hint: str
    tags: set[str] = field(default_factory=set)


@dataclass
class OutcomeAid:
    id: str
    label: str
    help_text: str
    strength: int
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


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["unease"] < THRESHOLD:
            continue
        sig = ("foreshadow", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("path").meters["warning"] += 1
        out.append("__foreshadow__")
    return out


def _r_truth_reveal(world: World) -> list[str]:
    out: list[str] = []
    clue = world.get("clue")
    if clue.meters["certainty"] < THRESHOLD:
        return out
    sig = ("reveal", clue.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("goal").meters["found"] += 1
    out.append("__reveal__")
    return out


CAUSAL_RULES = [
    Rule("foreshadow", "story", _r_foreshadow),
    Rule("truth_reveal", "story", _r_truth_reveal),
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


def reasonableness_gate(clue: Clue, place: Place, aid: OutcomeAid) -> bool:
    return clue.kind in {"phony", "real"} and place.shadowy and aid.strength >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for clue in CLUES:
            for aid in AIDS:
                if reasonableness_gate(clue, place, aid):
                    combos.append((place.id, clue.id, aid.id))
    return combos


def caution_score(clue: Clue) -> int:
    return 1 if clue.kind == "phony" else 3


def solve_outcome(clue: Clue, aid: OutcomeAid, delay: int) -> str:
    if clue.kind == "phony":
        return "false_alarm" if aid.strength >= 3 else "stalled"
    return "found" if aid.strength + delay >= 3 else "stalled"


def _do_search(world: World, clue: Clue, aid: OutcomeAid, narrate: bool = True) -> None:
    world.get("hero").meters["progress"] += 1
    world.get("hero").memes["bravery"] += 1
    if clue.kind == "phony":
        world.get("hero").memes["doubt"] += 1
    else:
        world.get("hero").memes["hope"] += 1
    if clue.kind == "real":
        world.get("clue").meters["certainty"] += 1
    propagate(world, narrate=narrate)


def set_scene(world: World, hero: Entity, nun: Entity, place: Place) -> None:
    world.say(
        f"{hero.id} and {nun.id} walked into {place.label}, where old stone walls "
        f"held the cool afternoon like a secret."
    )
    world.say(
        f"{hero.id} thought, If this place is hiding something, I have to notice it first."
    )


def foreshadow(world: World, hero: Entity, place: Place) -> None:
    world.say(
        f"A loose bell rope tapped the beam above them, and a draft curled under the door."
    )
    if place.shadowy:
        world.say(
            f"{hero.id} noticed the shadows near the aisle and felt the adventure sharpen."
        )


def discover_clue(world: World, clue: Clue, nun: Entity) -> None:
    world.say(
        f"Near a cracked bench, they found {clue.label}. It looked exciting, but {clue.story_hint}."
    )
    world.say(
        f"{nun.id} touched the edge and said it might be a phony clue."
    )


def inner_monologue(world: World, hero: Entity, clue: Clue) -> None:
    if clue.kind == "phony":
        world.say(
            f"{hero.id} thought, Maybe it wants me to hurry, but that would be silly. "
            f"A real trail should make sense."
        )
    else:
        world.say(
            f"{hero.id} thought, This feels different. The more I look, the more it seems real."
        )


def warn(world: World, nun: Entity, hero: Entity, clue: Clue, aid: OutcomeAid) -> None:
    world.get("nun").memes["care"] += 1
    world.say(
        f"{nun.id} said, 'Slow feet find better answers than quick feet,' and pointed to the little marks on the floor."
    )
    world.say(
        f"She also noticed {clue.truth_hint}, which made the old hint seem phony."
    )


def accept_help(world: World, hero: Entity, aid: OutcomeAid) -> None:
    hero.memes["trust"] += 1
    world.say(
        f"{hero.id} nodded and took {aid.label}. It was the kind of help that made the next step feel brave instead of rushed."
    )


def reveal(world: World, place: Place, clue: Clue) -> None:
    world.say(
        f"Following the better signs, they crossed {place.elev} and found the real hiding place at last."
    )
    world.say(
        f"{clue.label.capitalize()} turned out to matter after all, because it pointed them to the truth instead of the trick."
    )


def finish(world: World, hero: Entity, nun: Entity, aid: OutcomeAid) -> None:
    world.say(
        f"In the end, {hero.id} stood beside {nun.id} with the real prize in hand, and the old hall felt bright again."
    )
    world.say(
        f"{aid.help_text.capitalize()}, and the adventure was over with a calm smile instead of a rush."
    )


def tell(place: Place, clue: Clue, aid: OutcomeAid, delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(id="Mara", kind="character", type="girl", role="hero"))
    nun = world.add(Entity(id="Sister Bea", kind="character", type="nun", role="guide"))
    world.add(Entity(id="path", type="place", label=place.label))
    world.add(Entity(id="goal", type="goal", label="the hidden key"))
    world.add(Entity(id="clue", type="clue", label=clue.label))
    world.get("clue").meters["certainty"] = 0
    world.get("hero").memes["bravery"] = 1
    world.get("hero").memes["doubt"] = 0
    world.get("hero").memes["hope"] = 0
    world.get("nun").memes["care"] = 1

    set_scene(world, hero, nun, place)
    world.para()
    foreshadow(world, hero, place)
    discover_clue(world, clue, nun)
    inner_monologue(world, hero, clue)
    warn(world, nun, hero, clue, aid)

    world.para()
    _do_search(world, clue, aid)
    if clue.kind == "phony":
        world.say(
            f"The phony clue led to a dead end by the old well, and {hero.id} almost sighed."
        )
        world.say(
            f"But {nun.id} pointed to the scratch marks on the stone and said the right trail would still be nearby."
        )
        if aid.strength >= 3:
            world.say(
                f"{hero.id} took a breath, trusted the careful way, and kept going."
            )
        else:
            world.say(
                f"{hero.id} could not get far enough to solve it, and the trail faded into the dark."
            )
    else:
        world.say(
            f"The genuine clue brightened in {hero.id}'s hand, and the trail suddenly made sense."
        )

    world.para()
    if clue.kind == "real" or aid.strength >= 3:
        world.get("clue").meters["certainty"] += 1
        reveal(world, place, clue)
        finish(world, hero, nun, aid)
        outcome = "found"
    else:
        world.say(
            f"The day ended with the key still hidden, but {hero.id} had learned to watch for phony signs."
        )
        outcome = "stalled"

    world.facts.update(
        hero=hero,
        nun=nun,
        place=place,
        clue=clue,
        aid=aid,
        delay=delay,
        outcome=outcome,
        found=outcome == "found",
    )
    return world


PLACES = [
    Place("cloister", "the old cloister garden", True, "past the fountain", {"garden", "shadow"}),
    Place("library", "the candlelit archive", True, "up the spiral stair", {"library", "shadow"}),
    Place("courtyard", "the quiet courtyard at dusk", True, "near the cracked wall", {"courtyard", "shadow"}),
]

CLUES = [
    Clue("phony_note", "a phony note", "phony", "it promised treasure but pointed the wrong way", "the paper smelled fresh, like it had been dropped recently", {"phony"}),
    Clue("phony_map", "a phony map", "phony", "it had bold arrows that did not match the floor marks", "the ink was smeared where a hand had rubbed it", {"phony"}),
    Clue("genetic_tag", "a genetic tag", "real", "it named the old seed family and hinted where the lost key had been hidden", "the tag was tucked into a seed box with the same carved mark as the door", {"genetic"}),
]

AIDS = [
    OutcomeAid("lantern", "a lantern", "the lantern glowed softly and showed the floor marks", 3, {"light"}),
    OutcomeAid("string", "a spool of string", "the string let them follow the trail without getting lost", 2, {"tool"}),
    OutcomeAid("lantern_strong", "a bright lantern", "the bright lantern made the hidden mark easy to see", 4, {"light"}),
]

GIRL_NAMES = ["Mara", "Nina", "Tessa", "Lina", "Ruth", "Iris"]
BOY_NAMES = ["Evan", "Theo", "Noah", "Milo", "Jonah", "Pax"]


@dataclass
class StoryParams:
    place: str
    clue: str
    aid: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with a nun, a phony clue, and a genetic trail.")
    ap.add_argument("--place", choices=[p.id for p in PLACES])
    ap.add_argument("--clue", choices=[c.id for c in CLUES])
    ap.add_argument("--aid", choices=[a.id for a in AIDS])
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a young child that includes the words "nun", "{f["clue"].kind}", and "genetic".',
        f"Tell a foreshadowing adventure where {f['hero'].id} follows a clue in {f['place'].label} with a nun and learns to watch for phony signs.",
        f"Write a small mystery adventure with inner monologue, a careful nun, and a trail that turns out to be real instead of phony.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    nun = f["nun"]
    clue = f["clue"]
    aid = f["aid"]
    place = f["place"]
    items = [
        QAItem(
            question="Who went on the adventure?",
            answer=f"{hero.id} went with {nun.id} through {place.label}. They searched for a hidden prize in a careful, brave way."
        ),
        QAItem(
            question="What made the clue seem phony?",
            answer=f"{clue.truth_hint.capitalize()}. That is why the first clue looked phony and needed a slower look before anyone trusted it."
        ),
        QAItem(
            question="What helped them keep going?",
            answer=f"{aid.label} helped them see the trail better. It gave them enough light and guidance to keep the adventure safe and steady."
        ),
    ]
    if f["outcome"] == "found":
        items.append(
            QAItem(
                question="How did the story end?",
                answer=f"They found the hidden key and ended with relief. The phony clue did not win, because the real trail was there all along."
            )
        )
    else:
        items.append(
            QAItem(
                question="How did the story end?",
                answer="They did not finish the search that day, but they learned how to notice phony clues. The ending still points toward a better try later."
            )
        )
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    clue = f["clue"]
    qas = [
        QAItem(
            question="What is a nun?",
            answer="A nun is a woman who lives in a religious community and often helps and teaches other people."
        ),
        QAItem(
            question="What does phony mean?",
            answer="Phony means fake or not real. A phony clue can look exciting but still lead you the wrong way."
        ),
    ]
    if clue.kind == "real":
        qas.append(
            QAItem(
                question="What does genetic mean?",
                answer="Genetic means something about traits passed through families or living things. In this story, the genetic tag helped point to the real hiding place."
            )
        )
    else:
        qas.append(
            QAItem(
                question="What does genetic mean?",
                answer="Genetic means something about traits passed through families or living things. It is a real science word, even when a fake clue tries to borrow it."
            )
        )
    return qas


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p.id))
        if p.shadowy:
            lines.append(asp.fact("shadowy", p.id))
    for c in CLUES:
        lines.append(asp.fact("clue", c.id))
        lines.append(asp.fact("clue_kind", c.id, c.kind))
    for a in AIDS:
        lines.append(asp.fact("aid", a.id))
        lines.append(asp.fact("strength", a.id, a.strength))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, C, A) :- place(P), clue(C), aid(A), shadowy(P), strength(A, S), S >= sense_min.
phony(C) :- clue_kind(C, phony).
real(C) :- clue_kind(C, real).
outcome(found) :- clue_kind(C, real), aid(A), strength(A, S), S >= 3.
outcome(false_alarm) :- clue_kind(C, phony), aid(A), strength(A, S), S >= 3.
outcome(stalled) :- clue_kind(C, phony), aid(A), strength(A, S), S < 3.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_clue", params.clue),
        asp.fact("chosen_aid", params.aid),
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
        print("MISMATCH in ASP gate.")
    sample = generate(CURATED[0])
    _ = sample.story
    print("OK: generate() smoke test succeeded.")
    return rc


CURATED = [
    StoryParams("cloister", "phony_note", "lantern"),
    StoryParams("library", "genetic_tag", "lantern_strong"),
    StoryParams("courtyard", "phony_map", "string"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.clue is None or c[1] == args.clue)
              and (args.aid is None or c[2] == args.aid)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, aid = rng.choice(sorted(combos))
    return StoryParams(place, clue, aid)


def generate(params: StoryParams) -> StorySample:
    place = next(p for p in PLACES if p.id == params.place)
    clue = next(c for c in CLUES if c.id == params.clue)
    aid = next(a for a in AIDS if a.id == params.aid)
    world = tell(place, clue, aid)
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
        print(asp_program(show="#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
