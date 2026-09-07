#!/usr/bin/env python3
"""Gingham Magic: a small nursery-rhyme storyworld."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import itertools
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample


PROBLEMS = ("lost_star", "silent_bell", "dry_garden", "tangled_ribbon")
SOLUTIONS = ("sew_pocket", "borrow_song", "share_dew", "untie_rhyme")
VOICES = ("bright", "gentle", "bouncy")
NAMES = ("Nell", "Mina", "Pip", "Rose")
MAX_ACTIONS = 10


@dataclass
class StoryParams:
    hero: str = "Nell"
    problem: str = "lost_star"
    solution: str = "sew_pocket"
    voice: str = "bright"
    world_seed: int = 777
    prose_seed: int = 42


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Event:
    id: int
    kind: str
    actor: str
    data: dict
    facts: tuple[str, ...]
    causes: tuple[int, ...]
    state: dict


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.history: list[Event] = []
        self.facts: dict[str, int] = {}
        self.outcome = ""

    def snapshot(self):
        return {
            "entities": {k: asdict(v) for k, v in self.entities.items()},
            "outcome": self.outcome,
        }

    def record(self, kind, actor, facts=(), needs=(), **data):
        missing = [f for f in needs if f not in self.facts]
        if missing:
            raise StoryError(f"{kind} needs earlier facts: {', '.join(missing)}.")
        causes = tuple(sorted({self.facts[f] for f in needs}))
        event = Event(len(self.history), kind, actor, data, tuple(facts), causes, self.snapshot())
        self.history.append(event)
        for fact in facts:
            self.facts[fact] = event.id


def validate_params(p: StoryParams):
    if p.problem not in PROBLEMS:
        raise StoryError(f"Unknown problem: {p.problem!r}.")
    if p.solution not in SOLUTIONS:
        raise StoryError(f"Unknown solution: {p.solution!r}.")
    if p.voice not in VOICES:
        raise StoryError(f"Unknown voice: {p.voice!r}.")
    if not isinstance(p.world_seed, int) or not isinstance(p.prose_seed, int):
        raise StoryError("Seeds must be integers.")
    if not p.hero or not p.hero[0].isupper():
        raise StoryError("The hero's name must begin with a capital letter.")


def compatible(p: StoryParams) -> bool:
    return {
        "lost_star": {"sew_pocket", "borrow_song"},
        "silent_bell": {"borrow_song", "untie_rhyme"},
        "dry_garden": {"share_dew", "untie_rhyme"},
        "tangled_ribbon": {"sew_pocket", "untie_rhyme"},
    }[p.problem].__contains__(p.solution)


def build_world(p: StoryParams) -> World:
    validate_params(p)
    if not compatible(p):
        raise StoryError(f"The solution {p.solution!r} cannot mend the problem {p.problem!r}.")
    w = World(p)
    w.entities = {
        "nell": Entity("nell", p.hero, "child", "gingham_lane",
                       memes={"hope": 1, "patience": 1}),
        "moon": Entity("moon", "the moon", "magic", "sky",
                       meters={"light": 3}),
        "star": Entity("star", "the little star", "magic", "sky",
                       meters={"shine": 3}),
        "bell": Entity("bell", "the silver bell", "thing", "tower",
                       meters={"sound": 0}),
        "garden": Entity("garden", "the thirsty garden", "place", "gingham_lane",
                         meters={"water": 0, "flowers": 0}),
        "ribbon": Entity("ribbon", "the red ribbon", "thing", "gingham_lane",
                         meters={"knots": 3}),
        "pocket": Entity("pocket", "the gingham pocket", "thing", "apron",
                         meters={"open": 0}),
        "dew": Entity("dew", "a pearl of dew", "magic", "moonflower",
                      meters={"water": 2}),
        "song": Entity("song", "a borrowed song", "magic", "birdhouse",
                       meters={"notes": 3}),
    }
    w.record("opening", "nell", facts=("problem_seen",),
             problem=p.problem, solution=p.solution)
    return w


def choose_action(w: World):
    p = w.params
    if "conflict_resolved" in w.facts:
        return "close"
    if p.problem == "lost_star":
        if "star_found" not in w.facts:
            return "find_star"
        if p.solution == "sew_pocket" and "pocket_ready" not in w.facts:
            return "sew_pocket"
        if p.solution == "borrow_song" and "song_borrowed" not in w.facts:
            return "borrow_song"
        return "return_star"
    if p.problem == "silent_bell":
        if p.solution == "borrow_song" and "song_borrowed" not in w.facts:
            return "borrow_song"
        if p.solution == "untie_rhyme" and "rhyme_loosed" not in w.facts:
            return "untie_rhyme"
        return "ring_bell"
    if p.problem == "dry_garden":
        if p.solution == "share_dew" and "dew_shared" not in w.facts:
            return "share_dew"
        if p.solution == "untie_rhyme" and "rhyme_loosed" not in w.facts:
            return "untie_rhyme"
        return "wake_flowers"
    if p.problem == "tangled_ribbon":
        if p.solution == "sew_pocket" and "pocket_ready" not in w.facts:
            return "sew_pocket"
        if p.solution == "untie_rhyme" and "rhyme_loosed" not in w.facts:
            return "untie_rhyme"
        return "free_ribbon"
    return "close"


def execute(w: World, action: str):
    p = w.params
    if action == "find_star":
        w.entities["star"].location = "gingham_lane"
        w.record(action, "nell", facts=("star_found",), needs=("problem_seen",))
    elif action == "sew_pocket":
        w.entities["pocket"].meters["open"] = 1
        w.record(action, "nell", facts=("pocket_ready",), needs=("problem_seen",))
    elif action == "borrow_song":
        w.entities["song"].location = "nell"
        w.record(action, "nell", facts=("song_borrowed",), needs=("problem_seen",))
    elif action == "return_star":
        if p.solution == "sew_pocket":
            if "pocket_ready" not in w.facts:
                raise StoryError("The gingham pocket is not ready.")
            w.entities["star"].location = "pocket"
        else:
            if "song_borrowed" not in w.facts:
                raise StoryError("The borrowed song has not been found.")
            w.entities["star"].location = "sky"
        w.entities["nell"].memes["hope"] = 2
        w.outcome = "star_restored"
        w.record(action, "nell", facts=("conflict_resolved",), needs=("star_found",))
    elif action == "untie_rhyme":
        w.entities["ribbon"].meters["knots"] = 0
        w.record(action, "nell", facts=("rhyme_loosed",), needs=("problem_seen",))
    elif action == "ring_bell":
        if p.solution == "borrow_song" and "song_borrowed" not in w.facts:
            raise StoryError("The bell needs a song to wake its silver sound.")
        if p.solution == "untie_rhyme" and "rhyme_loosed" not in w.facts:
            raise StoryError("The bell's rhyme is still knotted.")
        w.entities["bell"].meters["sound"] = 3
        w.outcome = "bell_awake"
        w.record(action, "nell", facts=("conflict_resolved",), needs=("problem_seen",))
    elif action == "share_dew":
        if w.entities["dew"].meters["water"] < 2:
            raise StoryError("There is not enough dew to share.")
        w.entities["dew"].meters["water"] = 0
        w.entities["garden"].meters.update(water=2, flowers=3)
        w.outcome = "garden_bloomed"
        w.record(action, "nell", facts=("dew_shared", "conflict_resolved"), needs=("problem_seen",))
    elif action == "wake_flowers":
        if p.solution == "untie_rhyme" and "rhyme_loosed" not in w.facts:
            raise StoryError("The flower rhyme remains tangled.")
        w.entities["garden"].meters.update(water=1, flowers=3)
        w.outcome = "garden_bloomed"
        w.record(action, "nell", facts=("conflict_resolved",), needs=("problem_seen",))
    elif action == "free_ribbon":
        if p.solution == "sew_pocket" and "pocket_ready" not in w.facts:
            raise StoryError("The pocket must hold the ribbon's loose end.")
        if p.solution == "untie_rhyme" and "rhyme_loosed" not in w.facts:
            raise StoryError("The ribbon's rhyme is still knotted.")
        w.entities["ribbon"].meters["knots"] = 0
        w.outcome = "ribbon_freed"
        w.record(action, "nell", facts=("conflict_resolved",), needs=("problem_seen",))
    elif action == "close":
        if not w.outcome:
            raise StoryError("The tale cannot close before its problem is solved.")
        w.record("close", "nell", facts=("ending",), needs=("conflict_resolved",))
    else:
        raise StoryError(f"Unknown action {action!r}.")


def simulate(p: StoryParams) -> World:
    w = build_world(p)
    for _ in range(MAX_ACTIONS):
        execute(w, choose_action(w))
        if "ending" in w.facts:
            return w
    raise StoryError("The nursery rhyme did not reach an ending.")


class Teller:
    def __init__(self, w: World):
        self.w = w
        self.p = w.params
        self.rng = random.Random(self.p.prose_seed)
        self.parts = []
        self.qa = []

    def pick(self, *values):
        return self.rng.choice(values)

    def tell(self, text):
        self.parts.append(text)

    def run(self):
        p = self.p
        problem = p.problem
        if problem == "lost_star":
            self.tell(self.pick(
                f"On gingham lane, {p.hero} found a star in the rain.",
                f"{p.hero} walked by the gingham gate when a little star fell from the sky.",
            ))
            self.tell(self.pick(
                f'"I have lost my place," said the star. "{p.hero}, can you help me?"',
                f'"I am not where I belong," whispered the star. "{p.hero}, what shall we do?"',
            ))
            self.tell(self.pick(
                f'"We will mend this," said {p.hero}.',
                f'"Do not fret," {p.hero} replied. "A small light can still find a large sky."',
            ))
            self.qa.append(QAItem("Where did the star fall?",
                                  "The little star fell onto gingham lane in the rain."))
            if p.solution == "sew_pocket":
                self.tell(f"{p.hero} stitched a pocket from gingham cloth, wide and warm.")
                self.tell(f'"Stay here while I sew," said {p.hero}. The star glowed inside the pocket.')
                self.tell("Then the pocket opened like a tiny door, and the star sprang home.")
                self.qa.append(QAItem("How did the gingham help?",
                                      "The gingham became a pocket that safely held the star until it could return to the sky."))
            else:
                self.tell(f"{p.hero} borrowed a bright song from a bird in the old tree.")
                self.tell(f'"Sing with me," said {p.hero}. "The sky remembers songs."')
                self.tell("The song rose, the star heard its tune, and it climbed back into the blue.")
                self.qa.append(QAItem("Why did the song help?",
                                      "The borrowed song called to the star and guided it back into the sky."))
        elif problem == "silent_bell":
            self.tell(f"At the gingham tower, {p.hero} found the silver bell asleep.")
            self.tell(f'"Wake, bell, wake!" cried {p.hero}. "Why will you not ring?"')
            self.tell('"My rhyme is tied in a knot," sighed the bell.')
            self.qa.append(QAItem("Why was the bell silent?",
                                  "Its magic rhyme was tied in a knot, so its silver sound could not wake."))
            if p.solution == "borrow_song":
                self.tell(f"{p.hero} borrowed a song from a thrush beneath the gingham eaves.")
                self.tell(f'"Try this tune," said {p.hero}. "Let it loosen what is tight."')
                self.tell("The bell listened, then rang ding-dong, bright as morning.")
            else:
                self.tell(f"{p.hero} spoke the old rhyme backward, then forward, beside the gingham tower.")
                self.tell(f'"One word for each knot," said {p.hero}. "And one bell for each word."')
                self.tell("The rhyme came loose, and the bell rang ding-dong across the lane.")
            self.qa.append(QAItem("How did the bell wake?",
                                  "The hero used a magical song or rhyme to loosen the knot and restore the bell's ringing."))
        elif problem == "dry_garden":
            self.tell(f"Behind the gingham gate, {p.hero} found a garden pale and dry.")
            self.tell(f'"Thirsty flowers, what can I do?" asked {p.hero}.')
            self.tell('"We need a little magic water," said the moonflower.')
            self.qa.append(QAItem("What was wrong with the garden?",
                                  "The flowers were pale and dry because the garden had no magical water."))
            if p.solution == "share_dew":
                self.tell(f"{p.hero} gathered a pearl of dew from the gingham moonflower.")
                self.tell(f'"One drop for you, one drop for you," said {p.hero}, sharing it fairly.')
                self.tell("Three flowers lifted their heads, and the garden bloomed.")
            else:
                self.tell(f"{p.hero} untied the garden's old rhyme beneath the gingham gate.")
                self.tell(f'"Rain in the rhyme, rain in the ground," sang {p.hero}.')
                self.tell("A silver sprinkle fell, and every flower opened wide.")
            self.qa.append(QAItem("What changed the garden?",
                                  "Shared magical dew or an untied rain rhyme gave the flowers enough water to bloom."))
        else:
            self.tell(f"By the gingham gate, {p.hero} found a red ribbon tied in three hard knots.")
            self.tell(f'"I cannot dance," cried the ribbon. "These knots hold fast!"')
            self.tell(f'"Then we shall find the loose end," said {p.hero}.')
            self.qa.append(QAItem("Why could the ribbon not dance?",
                                  "Three tight knots held the red ribbon still."))
            if p.solution == "sew_pocket":
                self.tell(f"{p.hero} sewed a gingham pocket around the ribbon's loose end.")
                self.tell(f'"Hold still, little end," said {p.hero}. "Now I can pull without losing you."')
                self.tell("The knots slipped free, and the ribbon danced around the gingham gate.")
            else:
                self.tell(f"{p.hero} sang the ribbon's rhyme backward beside the gingham gate.")
                self.tell(f'"Knot be gone and end be found," sang {p.hero}.')
                self.tell("The magic rhyme loosened every knot, and the ribbon danced.")
            self.qa.append(QAItem("How was the ribbon freed?",
                                  "The gingham pocket held its loose end, or the magic rhyme loosened all three knots."))
        self.tell(self.pick(
            f"Then {p.hero} went home beneath the moon, and the gingham cloth waved like a little flag.",
            f"The lane grew bright again, and {p.hero} skipped home while the gingham gate swung softly.",
        ))
        self.qa.append(QAItem("What proved the problem was solved?",
                                  "The star returned, the bell rang, the garden bloomed, or the ribbon danced, while the hero went home."))
        return StorySample(
            params=p,
            story="\n\n".join(self.parts),
            prompts=[f"Write a Nursery Rhyme about {p.hero}, gingham, and Magic."],
            story_qa=self.qa,
            world_qa=[
                QAItem("What material is central to this world?",
                        "Gingham is the cheerful cloth that appears on the lane, gate, or magical pocket.")
            ],
            world=self.w,
        )


ASP_RULES = """
compatible(lost_star,sew_pocket).
compatible(lost_star,borrow_song).
compatible(silent_bell,borrow_song).
compatible(silent_bell,untie_rhyme).
compatible(dry_garden,share_dew).
compatible(dry_garden,untie_rhyme).
compatible(tangled_ribbon,sew_pocket).
compatible(tangled_ribbon,untie_rhyme).
#show compatible/2.
"""


def asp_facts():
    from asp import fact
    return "\n".join(fact("problem", p) for p in PROBLEMS) + "\n" + \
           "\n".join(fact("solution", s) for s in SOLUTIONS)


def asp_combos():
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + ASP_RULES), "compatible"))


def generate(params: StoryParams) -> StorySample:
    if not compatible(params):
        raise StoryError("That solution does not fit the chosen problem.")
    return Teller(simulate(params)).run()


def verify():
    expected = {(p, s) for p in PROBLEMS for s in SOLUTIONS
                if s in {
                    "lost_star": {"sew_pocket", "borrow_song"},
                    "silent_bell": {"borrow_song", "untie_rhyme"},
                    "dry_garden": {"share_dew", "untie_rhyme"},
                    "tangled_ribbon": {"sew_pocket", "untie_rhyme"},
                }[p]}
    if asp_combos() != expected:
        raise StoryError("Python and ASP disagree about compatible paths.")
    count = 0
    for problem, solution in expected:
        p = StoryParams(problem=problem, solution=solution)
        sample = generate(p)
        if len(sample.story_qa) < 3 or "gingham" not in sample.story.lower():
            raise StoryError("A generated tale lacks grounded prose or QA.")
        count += 1
    print(f"OK: {count} causal nursery-rhyme paths; ASP parity; dialogue checked.")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", dest="world_seed", type=int, default=777)
    parser.add_argument("--prose-seed", type=int, default=42)
    parser.add_argument("--hero", choices=NAMES)
    parser.add_argument("--problem", choices=PROBLEMS)
    parser.add_argument("--solution", choices=SOLUTIONS)
    parser.add_argument("--voice", choices=VOICES)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args, rng, index=0, sample=False):
    p = StoryParams(world_seed=args.world_seed + index,
                    prose_seed=args.prose_seed + index)
    for name, values in (
        ("hero", NAMES), ("problem", PROBLEMS),
        ("solution", SOLUTIONS), ("voice", VOICES)
    ):
        value = getattr(args, name)
        setattr(p, name, value if value is not None else rng.choice(values) if sample else getattr(p, name))
    if not compatible(p):
        if args.solution is None:
            choices = {
                "lost_star": ("sew_pocket", "borrow_song"),
                "silent_bell": ("borrow_song", "untie_rhyme"),
                "dry_garden": ("share_dew", "untie_rhyme"),
                "tangled_ribbon": ("sew_pocket", "untie_rhyme"),
            }[p.problem]
            p.solution = rng.choice(choices) if sample else choices[0]
        else:
            raise StoryError("The chosen solution does not fit the chosen problem.")
    return p


def emit(sample, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps({
            "state": sample.world.snapshot(),
            "history": [asdict(e) for e in sample.world.history],
        }, indent=2))


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        if args.n < 1:
            raise StoryError("-n must be positive.")
        if args.show_asp:
            print(asp_facts() + "\n" + ASP_RULES)
            return 0
        if args.verify:
            verify()
            return 0
        if args.asp:
            print(json.dumps(sorted(asp_combos())))
            return 0
        rng = random.Random(args.world_seed)
        if args.all:
            params = []
            for problem, solution in sorted(asp_combos()):
                if args.problem and args.problem != problem:
                    continue
                if args.solution and args.solution != solution:
                    continue
                p = resolve_params(args, rng)
                p.problem, p.solution = problem, solution
                params.append(p)
        else:
            params = [resolve_params(args, rng, i, sample=args.n > 1)
                      for i in range(args.n)]
        samples = [generate(p) for p in params]
        if args.json:
            payload = [s.to_dict() for s in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload,
                             ensure_ascii=False, indent=2))
        else:
            for i, sample in enumerate(samples):
                emit(sample, trace=args.trace, qa=args.qa,
                     header=f"\n### Story {i + 1}\n" if len(samples) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
