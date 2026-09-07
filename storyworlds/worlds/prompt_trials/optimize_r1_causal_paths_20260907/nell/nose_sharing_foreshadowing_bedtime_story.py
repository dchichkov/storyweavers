#!/usr/bin/env python3
"""A gentle bedtime story about a nose, sharing, and noticing clues in time."""

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


PROBLEMS = ("cold", "scent", "shadow", "sneeze")
SOLUTIONS = ("lantern", "sharing", "blanket", "bell")
VOICES = ("tender", "playful", "quiet")
NAMES = ("Nell", "Mara", "Pip", "Lina")
ANIMALS = ("rabbit", "fox", "mouse")
MAX_ACTIONS = 12


@dataclass
class StoryParams:
    hero: str = "Nell"
    friend: str = "rabbit"
    problem: str = "cold"
    solution: str = "sharing"
    voice: str = "tender"
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
    beliefs: dict[str, str] = field(default_factory=dict)


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
            "entities": {key: asdict(value) for key, value in self.entities.items()},
            "outcome": self.outcome,
        }

    def record(self, kind, actor, *, facts=(), needs=(), **data):
        if any(item not in self.facts for item in needs):
            raise StoryError(f"{kind} needs an earlier clue.")
        causes = tuple(sorted({self.facts[item] for item in needs}))
        event = Event(
            id=len(self.history),
            kind=kind,
            actor=actor,
            data=data,
            facts=tuple(facts),
            causes=causes,
            state=self.snapshot(),
        )
        self.history.append(event)
        for item in facts:
            self.facts[item] = event.id


def validate_params(p: StoryParams):
    if p.problem not in PROBLEMS:
        raise StoryError(f"Unknown problem: {p.problem!r}.")
    if p.solution not in SOLUTIONS:
        raise StoryError(f"Unknown solution: {p.solution!r}.")
    if p.voice not in VOICES:
        raise StoryError(f"Unknown voice: {p.voice!r}.")
    if not p.hero or not p.hero[0].isupper():
        raise StoryError("The hero's name must begin with a capital letter.")
    if type(p.world_seed) is not int or type(p.prose_seed) is not int:
        raise StoryError("Seeds must be integers.")


def build_world(p: StoryParams) -> World:
    validate_params(p)
    w = World(p)
    w.entities = {
        "hero": Entity("hero", p.hero, "character", "cottage",
                       memes={"kindness": 1, "curiosity": 1}),
        "friend": Entity("friend", f"the {p.friend}", "character", "cottage",
                         meters={"warmth": 0, "comfort": 0},
                         memes={"worry": 1}),
        "nose": Entity("nose", "the little nose", "body", "cottage",
                       meters={"sensitivity": 1}, memes={"tickle": 0}),
        "moon": Entity("moon", "the moon", "light", "sky",
                       meters={"brightness": 1}),
        "blanket": Entity("blanket", "the patchwork blanket", "object", "bed",
                          meters={"warmth": 3}),
        "lantern": Entity("lantern", "the small lantern", "object", "shelf",
                          meters={"brightness": 2}),
        "bell": Entity("bell", "the silver bell", "object", "bed",
                       meters={"sound": 2}),
        "mint": Entity("mint", "the mint leaves", "object", "garden",
                       meters={"scent": 2}),
        "pillow": Entity("pillow", "the soft pillow", "object", "bed",
                         meters={"comfort": 2}),
    }
    w.record(
        "opening",
        "hero",
        facts=("bedtime", "friend_present"),
        problem=p.problem,
        solution=p.solution,
    )
    return w


def simulate(p: StoryParams) -> World:
    w = build_world(p)
    problem = p.problem
    solution = p.solution

    if problem == "cold":
        w.entities["friend"].meters["warmth"] = 0
        w.record("shiver", "friend", facts=("cold_seen",), needs=("friend_present",))
        w.entities["hero"].beliefs["need"] = "warmth"
        w.record("notice_need", "hero", facts=("need_known",), needs=("cold_seen",))
        if solution == "sharing":
            w.entities["blanket"].location = "shared_bed"
            w.entities["friend"].meters["warmth"] = 3
            w.entities["hero"].meters = {"warmth": 2}
            w.record("share_blanket", "hero", facts=("warmth_shared",), needs=("need_known",))
        elif solution == "blanket":
            w.entities["blanket"].location = "friend"
            w.entities["friend"].meters["warmth"] = 3
            w.record("give_blanket", "hero", facts=("warmth_given",), needs=("need_known",))
        else:
            raise StoryError("A cold needs a blanket or a sharing plan.")

    elif problem == "scent":
        w.entities["mint"].location = "garden"
        w.entities["nose"].memes["tickle"] = 1
        w.record("sniff", "friend", facts=("scent_found",), needs=("friend_present",))
        w.entities["hero"].beliefs["need"] = "fresh_scent"
        w.record("learn_scent", "hero", facts=("scent_known",), needs=("scent_found",))
        if solution == "sharing":
            w.entities["mint"].location = "shared_pillow"
            w.record("share_mint", "hero", facts=("scent_shared",), needs=("scent_known",))
        elif solution == "lantern":
            w.entities["lantern"].location = "garden"
            w.record("light_path", "hero", facts=("path_lit",), needs=("scent_known",))
            w.entities["mint"].location = "bed"
            w.record("bring_mint", "hero", facts=("mint_brought",), needs=("path_lit",))
        else:
            raise StoryError("A hidden scent needs sharing or a lighted path.")

    elif problem == "shadow":
        w.entities["friend"].memes["worry"] = 2
        w.record("shadow_seen", "friend", facts=("shadow_seen",), needs=("friend_present",))
        w.entities["hero"].beliefs["need"] = "reassurance"
        w.record("notice_shadow", "hero", facts=("shadow_known",), needs=("shadow_seen",))
        if solution == "lantern":
            w.entities["lantern"].location = "bed"
            w.entities["lantern"].meters["brightness"] = 3
            w.record("light_shadow", "hero", facts=("shadow_lit",), needs=("shadow_known",))
        elif solution == "sharing":
            w.entities["friend"].memes["worry"] = 0
            w.record("share_courage", "hero", facts=("courage_shared",), needs=("shadow_known",))
        else:
            raise StoryError("A shadow needs a lantern or shared courage.")

    else:
        w.entities["nose"].memes["tickle"] = 2
        w.record("nose_twitches", "friend", facts=("tickle_seen",), needs=("friend_present",))
        w.entities["hero"].beliefs["need"] = "quiet"
        w.record("notice_tickle", "hero", facts=("tickle_known",), needs=("tickle_seen",))
        if solution == "bell":
            w.entities["bell"].location = "door"
            w.record("ring_bell", "hero", facts=("bell_rung",), needs=("tickle_known",))
        elif solution == "sharing":
            w.entities["hero"].memes["patience"] = 1
            w.entities["friend"].memes["worry"] = 0
            w.record("share_laughter", "hero", facts=("laughter_shared",), needs=("tickle_known",))
        else:
            raise StoryError("A tickling nose needs a bell or patient sharing.")

    w.outcome = f"{problem}_{solution}"
    w.record("settle", "hero", facts=("settled",), needs=tuple(
        fact for fact in ("warmth_shared", "warmth_given", "scent_shared", "mint_brought",
                          "shadow_lit", "courage_shared", "bell_rung", "laughter_shared")
        if fact in w.facts
    ))
    w.record("sleep", "hero", facts=("ending",), needs=("settled",))
    validate_world(w)
    return w


def validate_world(w: World):
    if "ending" not in w.facts or not w.outcome:
        raise StoryError("The bedtime story must reach sleep.")
    if w.entities["nose"].id != "nose":
        raise StoryError("The nose must remain part of the world.")
    for event in w.history:
        if any(parent >= event.id for parent in event.causes):
            raise StoryError("An event cannot depend on a future event.")


class Teller:
    def __init__(self, world: World):
        self.world = world
        self.p = world.params
        self.rng = random.Random(self.p.prose_seed)
        self.lines: list[str] = []
        self.qa: list[QAItem] = []
        self.context = {
            "hero": self.p.hero,
            "friend": self.p.friend,
        }

    def say(self, *choices):
        self.lines.append(self.rng.choice(choices))

    def dialogue(self, options):
        first = self.rng.choice(options)
        for speaker, line in first:
            name = self.p.hero if speaker == "hero" else f"the {self.p.friend}"
            self.lines.append(f'"{line}" {name} said.')

    def render(self):
        for event in self.world.history:
            self.event(event)
        return StorySample(
            params=self.p,
            story="\n\n".join(self.lines),
            prompts=[f"Write a gentle bedtime story in which {self.p.hero} notices a clue and shares comfort with a {self.p.friend}."],
            story_qa=self.qa,
            world_qa=[
                QAItem("What part of the body is central to this story?",
                       "The nose is central because it notices a tickle or a scent before bedtime."),
                QAItem("What makes the story a sharing story?",
                       "The characters share comfort, courage, a useful object, or a laugh instead of keeping help to themselves."),
            ],
            world=self.world,
        )

    def event(self, e: Event):
        k = e.kind
        if k == "opening":
            self.say(
                f"At bedtime, {self.p.hero} tucked the little {self.p.friend} into the cottage bed.",
                f"The moon climbed above the roof while {self.p.hero} and the {self.p.friend} prepared for sleep.",
                f"The room grew quiet, but {self.p.hero} was not alone. The {self.p.friend} was staying the night.",
            )
            self.dialogue((
                (("friend", "May I stay until the moon is high?"),
                 ("hero", "You may stay until the moon is gone.")),
                (("friend", "Will you listen if my nose tells me something?"),
                 ("hero", "I will listen carefully.")),
            ))
            self.say(
                "Neither friend knew that the first small clue was a nose already twitching at the edge of the blanket.",
                "The quiet room held a tiny warning: a little nose had begun to notice something.",
            )
            self.qa.append(QAItem("Who stayed for bedtime?",
                                   f"The little {self.p.friend} stayed with {self.p.hero} in the cottage bed."))
        elif k == "shiver":
            self.say(
                f"The {self.p.friend} shivered, and the bed gave a soft, worried creak.",
                f"A small shiver ran through the {self.p.friend}. {self.p.hero} saw it before the room grew colder.",
            )
            self.dialogue((
                (("friend", "I am not sleepy. I am cold."),
                 ("hero", "Thank you for telling me.")),
            ))
            self.qa.append(QAItem("What clue showed that the friend was cold?",
                                   f"The {self.p.friend} shivered in the bed, which showed {self.p.hero} that warmth was needed."))
        elif k == "sniff":
            self.say(
                "The little nose lifted and sniffed. A cool minty smell slipped in from the garden.",
                "The nose twitched toward the window, where the night carried the fresh scent of mint.",
            )
            self.dialogue((
                (("friend", "Do you smell that?"),
                 ("hero", "Mint. We can follow the clue together.")),
            ))
            self.qa.append(QAItem("What did the nose discover?",
                                   "It discovered the fresh scent of mint drifting in from the garden."))
        elif k == "shadow_seen":
            self.say(
                "A long shadow climbed the wall when a branch moved outside.",
                "The moon drew a tall shadow across the wall, and the {friend} curled close.".format(**self.context),
            )
            self.dialogue((
                (("friend", "The shadow looks enormous."),
                 ("hero", "We can find what made it.")),
            ))
            self.qa.append(QAItem("Why did the friend feel worried?",
                                   "A moving branch made a long shadow on the wall, and the shadow looked enormous in the moonlight."))
        elif k == "nose_twitches":
            self.say(
                "The nose twitched once, then twice, as if a feather were dancing inside it.",
                "A tiny tickle visited the nose and made its owner blink up at the moon.",
            )
            self.dialogue((
                (("friend", "I think a sneeze is hiding in my nose."),
                 ("hero", "Then we will wait gently for it.")),
            ))
            self.qa.append(QAItem("What was happening to the nose?",
                                   "It was twitching because a tickle made a sneeze feel close."))
        elif k in ("notice_need", "learn_scent", "notice_shadow", "notice_tickle"):
            self.say(
                f"{self.p.hero} listened to the clue instead of turning away.",
                f"{self.p.hero} watched the small sign again and understood what kind of help was needed.",
            )
        elif k == "share_blanket":
            self.say(
                f"{self.p.hero} pulled the patchwork blanket over both of them. Its warm squares covered two sleepy shoulders.",
                f"Instead of keeping the blanket, {self.p.hero} opened it wide so the {self.p.friend} could share its warmth.",
            )
            self.dialogue((
                (("friend", "Your blanket is warm."),
                 ("hero", "It is warmer when we share it.")),
            ))
            self.qa.append(QAItem("How did the friends solve the cold?",
                                   "They shared the patchwork blanket, so its warmth covered both friends."))
        elif k == "give_blanket":
            self.say(
                f"{self.p.hero} wrapped the patchwork blanket around the {self.p.friend} and sat close beside the bed.",
                f"The blanket moved from the foot of the bed to the shivering friend, who soon grew warm.",
            )
            self.dialogue((
                (("friend", "What will keep you warm?"),
                 ("hero", "Your smile will help, and I can sit close.")),
            ))
            self.qa.append(QAItem("What did {0} give to the friend?".format(self.p.hero),
                                   "The hero gave the friend the warm patchwork blanket."))
        elif k in ("share_mint", "bring_mint"):
            self.say(
                "They shared the mint leaves beneath the pillow, and the clean scent made the dark room feel fresh.",
                f"{self.p.hero} carried the mint to the bed, where both friends could breathe its gentle garden smell.",
            )
            self.dialogue((
                (("friend", "The mint smells like morning."),
                 ("hero", "Then morning can visit us early.")),
            ))
            self.qa.append(QAItem("How did the friends use the mint?",
                                   "They brought the mint close and shared its fresh scent beneath the pillow."))
        elif k == "light_path":
            self.say(
                f"{self.p.hero} lifted the lantern and made a small golden path to the garden.",
                "The lantern showed each stepping stone, so the night no longer felt like one large dark place.",
            )
        elif k == "light_shadow":
            self.say(
                f"{self.p.hero} lit the small lantern. The enormous shadow shrank into an ordinary branch.",
                "Golden light showed the truth: the frightening shape was only a branch waving outside.",
            )
            self.dialogue((
                (("friend", "It was only a branch."),
                 ("hero", "A clue can look large in the dark.")),
            ))
            self.qa.append(QAItem("What made the shadow seem small?",
                                   "The lantern revealed that the shadow came from an ordinary branch outside."))
        elif k == "share_courage":
            self.say(
                f"{self.p.hero} took the {self.p.friend}'s paw and shared a brave breath.",
                "They named three quiet things they could see, two they could hear, and one they could feel.",
            )
            self.dialogue((
                (("friend", "I can be brave if you are near."),
                 ("hero", "And I can be brave because you are here.")),
            ))
            self.qa.append(QAItem("How did the friends face the shadow?",
                                   "They shared courage by holding paws and noticing the real, quiet things around them."))
        elif k == "ring_bell":
            self.say(
                f"{self.p.hero} rang the silver bell once. The clear note gave the hiding sneeze a gentle path out.",
                "A single silver chime floated through the room, and the tickle loosened from the nose.",
            )
            self.dialogue((
                (("friend", "The sneeze heard the bell."),
                 ("hero", "Sometimes a small sound helps a small nose.")),
            ))
            self.qa.append(QAItem("What helped the tickle leave the nose?",
                                   "A gentle ring of the silver bell helped the tickle loosen and the sneeze come out."))
        elif k == "share_laughter":
            self.say(
                "They waited together. The sneeze arrived at last, and afterward they shared a soft, surprised laugh.",
                "The nose gave one enormous achoo, and two sleepy smiles answered it.",
            )
            self.dialogue((
                (("friend", "Achoo!"),
                 ("hero", "Bless you. That was a very brave sneeze.")),
            ))
            self.qa.append(QAItem("What did the friends share after the sneeze?",
                                   "They shared a soft laugh after the sneeze finally came out."))
        elif k == "settle":
            self.say(
                "The first clue had led to the right kindness, and the cottage became peaceful again.",
                "Once the small trouble had changed, the room settled like a feather on still water.",
            )
        elif k == "sleep":
            self.say(
                f"The nose grew still, the moon slid west, and {self.p.hero} and the {self.p.friend} fell asleep side by side.",
                f"Under the moon's pale watch, the friends slept close together, sharing the last warm hush of the night.",
            )
            self.dialogue((
                (("friend", "Good night."),
                 ("hero", "Good night. I will listen for every little clue.")),
            ))
            self.qa.append(QAItem("How did the story end?",
                                   f"{self.p.hero} and the {self.p.friend} fell asleep side by side after sharing the help they needed."))


ASP_RULES = """
valid_problem(cold).
valid_problem(scent).
valid_problem(shadow).
valid_problem(sneeze).
valid_solution(sharing).
valid_solution(lantern).
valid_solution(blanket).
valid_solution(bell).
compatible(cold,sharing).
compatible(cold,blanket).
compatible(scent,sharing).
compatible(scent,lantern).
compatible(shadow,sharing).
compatible(shadow,lantern).
compatible(sneeze,sharing).
compatible(sneeze,bell).
#show compatible/2.
"""


def asp_facts():
    from asp import fact
    return "\n".join(
        [fact("valid_problem", item) for item in PROBLEMS]
        + [fact("valid_solution", item) for item in SOLUTIONS]
    )


def asp_combos():
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "compatible"))


def generate(params: StoryParams) -> StorySample:
    return Teller(simulate(params)).render()


def verify():
    expected = {
        ("cold", "sharing"), ("cold", "blanket"),
        ("scent", "sharing"), ("scent", "lantern"),
        ("shadow", "sharing"), ("shadow", "lantern"),
        ("sneeze", "sharing"), ("sneeze", "bell"),
    }
    if asp_combos() != expected:
        raise StoryError("Python and ASP disagree about compatible bedtime paths.")
    for problem, solution in expected:
        sample = generate(StoryParams(problem=problem, solution=solution))
        if "nose" not in sample.story.lower():
            raise StoryError("Every story must include the nose.")
        if len(sample.story_qa) < 2:
            raise StoryError("Every story needs grounded questions.")
    print("OK: compatible paths, foreshadowed clues, dialogue, and endings verified.")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", dest="world_seed", type=int, default=777)
    parser.add_argument("--prose-seed", type=int, default=42)
    parser.add_argument("--hero", choices=NAMES)
    parser.add_argument("--friend", choices=ANIMALS)
    parser.add_argument("--problem", choices=PROBLEMS)
    parser.add_argument("--solution", choices=SOLUTIONS)
    parser.add_argument("--voice", choices=VOICES, default="tender")
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args, rng, index=0, sample=False):
    p = StoryParams(
        world_seed=args.world_seed + index,
        prose_seed=args.prose_seed + index,
        voice=args.voice,
    )
    choices = {
        "hero": NAMES,
        "friend": ANIMALS,
        "problem": PROBLEMS,
        "solution": SOLUTIONS,
    }
    for name, values in choices.items():
        chosen = getattr(args, name)
        setattr(p, name, chosen if chosen is not None else getattr(p, name))
    if sample:
        compatible = {
            "cold": ("sharing", "blanket"),
            "scent": ("sharing", "lantern"),
            "shadow": ("sharing", "lantern"),
            "sneeze": ("sharing", "bell"),
        }
        if args.problem is None:
            p.problem = rng.choice(PROBLEMS)
        if args.solution is None:
            p.solution = rng.choice(compatible[p.problem])
    validate_params(p)
    if (p.problem, p.solution) not in asp_combos():
        raise StoryError(f"The solution {p.solution!r} does not fit the problem {p.problem!r}.")
    return p


def emit(sample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps(
            {"state": sample.world.snapshot(), "history": [asdict(e) for e in sample.world.history]},
            indent=2,
        ))


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
                if args.problem is not None and args.problem != problem:
                    continue
                if args.solution is not None and args.solution != solution:
                    continue
                params.append(resolve_params(
                    argparse.Namespace(**{**vars(args), "problem": problem, "solution": solution}),
                    rng,
                    len(params),
                    sample=False,
                ))
        else:
            params = [
                resolve_params(args, rng, index, sample=args.n > 1)
                for index in range(args.n)
            ]

        samples = [generate(p) for p in params]
        if args.json:
            payload = [item.to_dict() for item in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload,
                             ensure_ascii=False, indent=2))
        else:
            for index, sample in enumerate(samples):
                emit(sample, trace=args.trace, qa=args.qa,
                     header=f"\n### Story {index + 1}\n" if len(samples) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
