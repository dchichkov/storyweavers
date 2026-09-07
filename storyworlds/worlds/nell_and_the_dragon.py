#!/usr/bin/env python3
"""Nell and the Dragon, adapted from the user's supplied story.

Value belongs to a character, not a price tag. The bird must be able to carry
an offer, approach without fear, and use it before the lost jewel comes free.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
import random
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    label: str
    kind: str = "thing"
    location: str = "home"
    owner: str = "nell"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    beliefs: dict[str, str] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    speaker: str = ""
    listener: str = ""
    revealed: str = ""
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Nell"
    need: str = "shine"
    solution: str = "trinkets"
    approach: str = "patient"
    jewel: str = "emerald"
    seed: int = 777


NEEDS = ("shine", "fasten", "softness")
APPROACHES = ("patient", "hasty")
NAMES = ("Nell", "Ada", "Kit", "Rose")
JEWELS = {"emerald": "green", "sapphire": "blue", "amethyst": "purple"}
# Weights and affordances are toy-world units, not claims about real magpies.
ITEMS = {
    "cap": dict(label="a bottle cap", weight=1, shine=2, fasten=0, softness=0),
    "glass": dict(label="a piece of blue glass", weight=1, shine=3, fasten=0, softness=0),
    "button": dict(label="one bright brass button", weight=1, shine=6, fasten=1, softness=0),
    "hoop": dict(label="a little loop of soft wire", weight=1, shine=1, fasten=6, softness=0),
    "wool": dict(label="a tuft of clean wool", weight=1, shine=0, fasten=0, softness=6),
}
SOLUTIONS = {"trinkets": ("cap", "glass", "button"),
             "repairs": ("cap", "glass", "hoop"),
             "bedding": ("cap", "glass", "wool")}
SHORT_NAMES = {"cap": "bottle cap", "glass": "glass", "button": "button",
               "hoop": "wire loop", "wool": "wool"}
CAPACITY = 2
SATISFACTION = 5
SAFE_DISTANCE = 8
GEM_METERS = dict(weight=1, shine=4, fasten=0, softness=0)


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {}
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def record(self, kind: str, text: str, *, question="", cause="", result=""):
        self.history.append(Event(kind=kind, text=text, question=question,
                                  cause=cause, result=result, state=self.snapshot()))

    def say(self, speaker: str, text: str, *, to="", reveal="", tag="said"):
        actor = self.entities[speaker]
        if reveal:
            if to not in self.entities or reveal not in actor.beliefs:
                raise StoryError("A speaker must know the information before sharing it.")
            self.entities[to].beliefs[reveal] = actor.beliefs[reveal]
        previous = self.history[-1] if self.history else None
        attribute = tag != "said" or previous is None or previous.kind != "speech" or previous.speaker == speaker
        if attribute:
            if text.endswith("?") and tag == "said":
                tag = "asked"
            if text.endswith(".") and not text.endswith("..."):
                text = text[:-1] + ","
        rendered = f'"{text}"' + (f" {actor.label} {tag}." if attribute else "")
        self.history.append(Event(kind="speech", text=rendered,
                                  speaker=speaker, listener=to, revealed=reveal,
                                  state=self.snapshot()))


def useful(need: str, item: dict) -> bool:
    return item["weight"] <= CAPACITY and item[need] >= SATISFACTION and item[need] > GEM_METERS[need]


def valid_combos() -> list[tuple[str, str]]:
    return [(need, solution) for need in NEEDS for solution, tray in SOLUTIONS.items()
            if any(useful(need, ITEMS[key]) for key in tray)]


def validate_params(params: StoryParams):
    if (params.need, params.solution) not in valid_combos():
        raise StoryError("The selected dish has nothing useful enough for this bird's need.")
    if params.approach not in APPROACHES or params.jewel not in JEWELS:
        raise StoryError("Unknown approach or jewel.")
    if not re.fullmatch(r"[A-Z][a-z]+", params.hero):
        raise StoryError("Use a simple capitalized name, such as Nell.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    world.entities = {
        "nell": Entity(id="nell", label=params.hero, kind="character", location="window",
                       memes={"curiosity": 1}, meters={"distance": 0}),
        "dragon": Entity(id="dragon", label="the dragon", kind="character", location="window", owner="dragon",
                         meters={"distance": 0, "claw_width": 8, "catch_reach": 12, "teeth": 1, "volume": 0},
                         memes={"pride": 1, "patience": 0, "relief": 0},
                         beliefs={"lost_jewel": params.jewel, "offered": "ruby"}),
        "bird": Entity(id="bird", label="the magpie", kind="character", location="nest", owner="bird",
                       meters={"capacity": CAPACITY, "satisfaction": SATISFACTION},
                       memes={"fear": 0}, beliefs={"need": params.need}),
        "tree": Entity(id="tree", label="a narrow pine tree", location="clearing", owner="",
                       meters={"fork_width": 2, "intact": 1}),
        "nest": Entity(id="nest", label="the nest", location="tree", owner="bird",
                       meters={"intact": 1, "need_met": 0}, beliefs={"occupant": "jewel"}),
        "jewel": Entity(id="jewel", label=params.jewel, location="nest", owner="dragon", meters=dict(GEM_METERS)),
        "ruby": Entity(id="ruby", label="a cabbage-sized ruby", location="dragon_claw", owner="dragon",
                       meters={"weight": 100, "shine": 10, "fasten": 0, "softness": 0}),
        "dish": Entity(id="dish", label="a little tin dish", meters={"on_ground": 0}),
    }
    for key, spec in ITEMS.items():
        world.entities[key] = Entity(id=key, label=spec["label"],
                                     meters={name: value for name, value in spec.items() if name != "label"})
    return world


def can_reach_without_damage(world: World) -> bool:
    return world.entities["dragon"].meters["claw_width"] <= world.entities["tree"].meters["fork_width"]


def safe_to_visit(world: World) -> bool:
    dragon, nell = world.entities["dragon"], world.entities["nell"]
    return (dragon.meters["distance"] >= SAFE_DISTANCE and nell.meters["distance"] >= SAFE_DISTANCE
            and dragon.meters["volume"] == 0 and dragon.meters["teeth"] == 0)


def preferred_offer(world: World) -> str | None:
    bird = world.entities["bird"]
    need = bird.beliefs["need"]
    candidates = [key for key, item in world.entities.items()
                  if item.location == "dish" and item.meters.get("weight", CAPACITY + 1) <= bird.meters["capacity"]
                  and item.meters.get(need, 0) >= bird.meters["satisfaction"]
                  and item.meters.get(need, 0) > world.entities["jewel"].meters[need]]
    return max(candidates, key=lambda key: world.entities[key].meters[need], default=None)


def set_dish(world: World):
    if "need" not in world.entities["nell"].beliefs:
        raise StoryError("Nell must observe the bird before choosing what to offer.")
    if world.entities["dish"].location != "home":
        raise StoryError("The dish is already in use.")
    world.entities["dish"].location = "clearing"
    world.entities["dish"].meters["on_ground"] = 1
    for key in SOLUTIONS[world.params.solution]:
        world.entities[key].location = "dish"


def visit_dish(world: World) -> str | None:
    bird = world.entities["bird"]
    if bird.location != "nest":
        raise StoryError("The bird is already carrying something or rearranging her nest.")
    if not world.entities["dish"].meters["on_ground"]:
        raise StoryError("There is no dish on the ground to inspect.")
    if not safe_to_visit(world):
        bird.memes["fear"] = 1
        return None
    bird.memes["fear"] = 0
    choice = preferred_offer(world)
    if choice is not None:
        world.entities[choice].location = "beak"
        world.entities[choice].owner = "bird"
        bird.location = "dish"
        bird.beliefs["selected"] = choice
    return choice


def return_to_nest(world: World):
    bird = world.entities["bird"]
    chosen = bird.beliefs.get("selected")
    if not chosen or bird.location != "dish" or world.entities[chosen].location != "beak":
        raise StoryError("The bird must take an offer before returning with it.")
    bird.location = "nest"


def install_offer(world: World):
    bird, nest, jewel = (world.entities[key] for key in ("bird", "nest", "jewel"))
    chosen = bird.beliefs.get("selected")
    if (not chosen or bird.location != "nest" or world.entities[chosen].location != "beak"
            or nest.beliefs["occupant"] != "jewel" or jewel.location != "nest"):
        raise StoryError("Only a real replacement at the nest can dislodge the jewel.")
    item, need = world.entities[chosen], bird.beliefs["need"]
    if item.meters[need] < bird.meters["satisfaction"] or item.meters[need] <= jewel.meters[need]:
        raise StoryError("The replacement does not satisfy the bird's need.")
    item.location = "nest"
    nest.beliefs["occupant"] = chosen
    nest.meters["need_met"] = 1
    jewel.location = "falling"


def catch_jewel(world: World):
    dragon, jewel = world.entities["dragon"], world.entities["jewel"]
    if jewel.location != "falling" or dragon.meters["distance"] > dragon.meters["catch_reach"]:
        raise StoryError("The dragon can catch only a falling jewel within reach.")
    jewel.location = "dragon_claw"
    dragon.memes.update(relief=1, pride=0.5)


def step_back(world: World):
    world.entities["nell"].meters["distance"] = SAFE_DISTANCE
    world.entities["dragon"].meters.update(distance=SAFE_DISTANCE, teeth=0, volume=0)
    world.entities["dragon"].memes["patience"] = 1


def generate(params: StoryParams) -> StorySample:
    w = build_world(params)
    nell, dragon, bird = (w.entities[key] for key in ("nell", "dragon", "bird"))
    name, jewel, color = params.hero, params.jewel, JEWELS[params.jewel]
    w.record("beginning", f"The dragon came to {name}'s window at half past four.")
    w.say("dragon", "I require a thief.")
    w.record("book_down", f"{name} put down her book.")
    for who, line in (("nell", "How good a thief?"), ("dragon", "Better than the one who has robbed me."),
                      ("nell", "What did they take?")):
        w.say(who, line)
    w.say("dragon", f"My {jewel}.", to="nell", reveal="lost_jewel")
    w.say("nell", "How big?")
    w.say("dragon", "Pea-sized.")
    w.record("look", f"{name} looked at him.")
    w.say("dragon", "I am allowed to like small things.")
    nell.location = dragon.location = "clearing"
    if can_reach_without_damage(w):
        raise StoryError("This premise requires a claw too wide for the tree's fork.")
    w.record("reach_risk", "The culprit was a magpie. She had installed the jewel in a nest at the top of a narrow pine tree. "
             "The dragon could reach it easily. Unfortunately, reaching it would demolish the tree.",
             question="Why did the dragon need help to recover his jewel?",
             cause="His claw could reach the nest, but it was too large to fit between the branches.",
             result="Taking the jewel that way would break the tree and the magpie's home.")
    for who, line in (("dragon", "I offered her a ruby."), ("nell", "What happened?"),
                      ("dragon", "She flew away."), ("nell", "Did you roar?"), ("dragon", "I explained."),
                      ("nell", "Loudly?"), ("dragon", "There was some emphasis.")):
        w.say(who, line)
    observations = {
        "shine": "The magpie returned. She brought a twig, fitted it into the nest, removed it, turned it round, "
                 "and fitted it again. Then she tilted the jewel until it caught the light.",
        "fasten": "The magpie returned with a twig. Each time she fitted it into the rim, it sprang loose. "
                  "She pushed the jewel against it, but the twig slipped again.",
        "softness": "The magpie returned with a feather. She tucked it into a hollow, settled down, then got up "
                    "and moved the jewel. The hard little bump was still in her way.",
    }
    nell.beliefs["need"] = bird.beliefs["need"]
    w.record("observe", f"{name} sat beneath the tree and watched. " + observations[bird.beliefs["need"]])
    w.say("nell", "Your ruby. Show me.")
    w.record("ruby_shown", "He opened his claw. It was the size of a cabbage.")
    if w.entities["ruby"].meters["weight"] <= bird.meters["capacity"]:
        raise StoryError("The unsuccessful ruby offer must be too heavy to carry.")
    nell.beliefs["ruby_problem"] = "too heavy to carry"
    w.say("nell", "Well, she can't carry that.", to="dragon", reveal="ruby_problem")
    w.say("dragon", "It is worth a kingdom.")
    w.say("nell", "She hasn't got a kingdom-sized pocket.")
    w.record("value_mismatch", "The dragon considered the ruby.",
             question="Why was the valuable ruby a poor offer?",
             cause="The ruby was cabbage-sized, much too heavy for the magpie to carry.",
             result=f"{name} pointed out that its value to a dragon did not make it usable by the bird.")
    w.say("dragon", "I may have approached this as a dragon.")
    if params.need == "fasten":
        w.say("nell", "She needs something to hold that twig.", to="dragon", reveal="need")
        w.say("dragon", "I could hold it.")
        w.say("nell", "Until next spring?")
        w.say("dragon", "I do have other appointments.")
    elif params.need == "softness":
        w.say("nell", "She needs something soft in that hollow.", to="dragon", reveal="need")
        w.say("dragon", "It is a very smooth jewel.")
        w.say("nell", "Try sleeping on it.")
        w.say("dragon", "I sleep on several thousand.")
        w.say("nell", "We may have found the difficulty.")
    set_dish(w)
    tray = SOLUTIONS[params.solution]
    labels = [w.entities[key].label for key in tray]
    w.record("offer_set", f"{name} borrowed a little tin dish from home. She put {labels[0]} in it, "
             f"{labels[1]}, and {labels[2]}. She set it beneath the tree.")
    nell.meters["distance"] = SAFE_DISTANCE
    dragon.meters["distance"] = 4
    bird.memes["fear"] = float(not safe_to_visit(w))
    w.record("move_away", "Then they moved away.")
    w.say("nell", "Further.")
    w.say("dragon", f"I can scarcely see my {jewel}.")
    w.say("nell", "She can still see your teeth.")
    step_back(w)
    w.record("clear_space", "He shut his mouth and took another careful step back.",
             question="Why did they move away from the dish?",
             cause="The dragon's nearby teeth made it unsafe for the magpie to approach.",
             result="He closed his mouth and both helpers waited at a distance, leaving the offer on the ground.")
    w.say("nell", "That helps.")
    if params.approach == "hasty":
        dragon.meters["distance"] = 4
        if visit_dish(w) is not None:
            raise StoryError("The bird should refuse a dish guarded by a nearby dragon.")
        w.record("interrupted", "The magpie leaned down. The dragon stepped forward with his claw held out. "
                 "She drew back into the branches.",
                 question="Why did the magpie draw back on her first attempt?",
                 cause="The dragon moved toward the dish before she had taken anything.",
                 result="She retreated, so he had to step back and give her room again.")
        w.say("dragon", "I was only getting ready.")
        w.say("nell", "She noticed.")
        w.say("dragon", "How will she know I want it back?")
        w.say("nell", "She isn't reading a contract. Let her choose.")
        step_back(w)
        w.record("retry_space", "He folded his claws against his chest and returned to their waiting place.")
    choice = visit_dish(w)
    if choice is None:
        raise StoryError("The bird could not safely take a useful offer.")
    short = SHORT_NAMES[choice]
    bird_choice_text = {"button": "She took the button.", "hoop": "She gripped the wire loop and tugged. Then she took it.",
                        "wool": "She pulled at the wool, gathering it into a soft bundle. Then she took it."}
    w.record("take_offer", "The magpie came down. She inspected the glass. She tipped the bottle cap over. "
             + bird_choice_text[choice])
    w.say("dragon", "Well, we've paid her.", tag="whispered")
    w.say("nell", "Wait.")
    return_to_nest(w)
    w.record("return_to_nest", "The bird returned to the nest.")
    install_offer(w)
    rearrangements = {
        "button": "There was a small, busy rearrangement. The brass button winked from the place where the jewel had been.",
        "hoop": "She hooked the loop around the troublesome twig. This time the twig stayed. She nudged away the jewel "
                "she had been using to prop it up.",
        "wool": "She worked the wool into the hollow. The jewel made a lump under the new lining, so she pushed it over the rim.",
    }
    w.record("replace_jewel", rearrangements[choice] + f" Then something {color} dropped through the branches.",
             question="What made the magpie let go of the jewel?",
             cause={"button": "She installed the bright button in the place where she had displayed the jewel.",
                    "hoop": "The wire loop held her loose twig, so the jewel was no longer needed as a prop.",
                    "wool": "She lined the hollow with wool and removed the hard jewel that made a lump underneath."}[choice],
             result="She pushed the jewel out only after carrying the useful replacement back to her nest.")
    catch_jewel(w)
    w.record("catch", f"The dragon caught it before it touched the grass. He stared at the {jewel} resting on his enormous claw.")
    w.say("dragon", "She threw it away.")
    w.say("nell", "She found something she liked better.")
    w.say("dragon", "But...")
    w.say("nell", {"button": "Yes. A button.", "hoop": "Yes. A bent bit of wire.", "wool": "Yes. A bit of wool."}[choice])
    dragon.beliefs["bird_values"] = short
    nell.location = dragon.location = "path_home"
    w.record("walk_home", f"They left the magpie settling her nest and took the path to {name}'s house.")
    w.say("dragon", "What do I owe you?")
    w.record("consider_payment", f"{name} thought.")
    w.say("nell", "A story. A true one. About somewhere you've been.")
    w.say("dragon", "I know some very long stories.")
    w.say("nell", "Good.")
    w.say("dragon", "And I occasionally make myself look rather magnificent.")
    w.say("nell", "I'll ask questions.")
    dragon.beliefs["payment_promised"] = "a true story about his travels"
    w.record("smile", "The dragon smiled.")
    w.say("dragon", "Yes. I rather thought you would.")
    w.record("ending", f"The {jewel} rested safely in his closed claw. Beside him, {name} was already thinking of her first question.",
             question="What payment did the helper ask for?",
             cause=f"{name} asked for a true story about somewhere the dragon had been, instead of a jewel.",
             result="He agreed to tell one, knowing that she would ask questions.")
    sample = StorySample(params=params, story="\n\n".join(event.text for event in w.history),
                         prompts=[f"Write a dialogue-rich story about {name}, a dragon's lost {jewel}, and a magpie. "
                                  "The helper must discover what the bird can actually use without damaging her home."],
                         story_qa=[QAItem(question=e.question, answer=f"{e.cause} {e.result}")
                                   for e in w.history if e.question], world_qa=[], world=w)
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    bird, nest, jewel = (world.entities[key] for key in ("bird", "nest", "jewel"))
    chosen = bird.beliefs.get("selected")
    if jewel.location != "dragon_claw" or jewel.owner != "dragon":
        raise StoryError("The original jewel must actually return to the dragon.")
    if (not chosen or world.entities[chosen].location != "nest" or world.entities[chosen].owner != "bird"
            or nest.beliefs["occupant"] != chosen or not nest.meters["need_met"]):
        raise StoryError("The bird must keep and use the chosen replacement.")
    if not world.entities["tree"].meters["intact"] or not nest.meters["intact"]:
        raise StoryError("The bird's home must survive the recovery.")
    kinds = [event.kind for event in world.history]
    steps = ("take_offer", "return_to_nest", "replace_jewel", "catch", "ending")
    if any(kinds.count(step) != 1 for step in steps) or [kinds.index(step) for step in steps] != sorted(kinds.index(step) for step in steps):
        raise StoryError("Taking, carrying, replacing, and catching must be separate events in order.")
    if len([event for event in world.history if event.speaker == "nell"]) < 15:
        raise StoryError("The helper needs a sustained conversation, not a narrated summary.")
    if len(sample.story_qa) < 5 or any(not e.cause or not e.result for e in world.history if e.question):
        raise StoryError("Story QA must include grounded causes and consequences.")


ASP_RULES = """
useful(N,I) :- need(N), item(I,W), capacity(C), W <= C,
               affinity(I,N,V), threshold(T), V >= T, jewel_value(N,J), V > J.
valid(N,S) :- solution(S), contains(S,I), useful(N,I).
#show valid/2.
"""


def asp_facts() -> str:
    from asp import fact
    facts = [fact("capacity", CAPACITY), fact("threshold", SATISFACTION)]
    for need in NEEDS:
        facts += [fact("need", need), fact("jewel_value", need, GEM_METERS[need])]
    for key, item in ITEMS.items():
        facts.append(fact("item", key, item["weight"]))
        facts += [fact("affinity", key, need, item[need]) for need in NEEDS]
    for solution, tray in SOLUTIONS.items():
        facts.append(fact("solution", solution))
        facts += [fact("contains", solution, key) for key in tray]
    return "\n".join(facts)


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "valid"))


def verify():
    if set(valid_combos()) != asp_combos():
        raise StoryError("Python and ASP disagree about usable offerings.")
    count = 0
    for need, solution in valid_combos():
        for approach in APPROACHES:
            for jewel in JEWELS:
                check_sample(generate(StoryParams(need=need, solution=solution, approach=approach, jewel=jewel)))
                count += 1
    print(f"OK: {count} story states; {len(valid_combos())} Python/ASP-compatible offers.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--need", choices=NEEDS)
    parser.add_argument("--solution", choices=tuple(SOLUTIONS))
    parser.add_argument("--approach", choices=APPROACHES)
    parser.add_argument("--jewel", choices=tuple(JEWELS))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, *, sample=False) -> StoryParams:
    choices = [(n, s) for n, s in valid_combos()
               if (args.need is None or args.need == n) and (args.solution is None or args.solution == s)]
    if not choices:
        raise StoryError("That dish does not satisfy the selected need.")
    need, solution = rng.choice(choices) if sample else choices[0]
    params = StoryParams(hero=args.hero or (rng.choice(NAMES) if sample else "Nell"),
                         need=need, solution=solution,
                         approach=args.approach or (rng.choice(APPROACHES) if sample else "patient"),
                         jewel=args.jewel or (rng.choice(tuple(JEWELS)) if sample else "emerald"), seed=args.seed)
    validate_params(params)
    return params


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for pair in sample.story_qa:
            print(f"\nQ: {pair.question}\nA: {pair.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps(dict(entities=sample.world.snapshot(),
                              history=[asdict(event) for event in sample.world.history]), indent=2))


def main() -> int:
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
        rng = random.Random(args.seed)
        if args.all:
            combinations = [(n, s, a) for n, s in valid_combos() for a in APPROACHES
                            if (args.need is None or args.need == n)
                            and (args.solution is None or args.solution == s)
                            and (args.approach is None or args.approach == a)]
            if not combinations:
                raise StoryError("No compatible variants match those options.")
            params = [resolve_params(argparse.Namespace(**(vars(args) | dict(need=n, solution=s, approach=a))), rng)
                      for n, s, a in combinations]
        else:
            params = [resolve_params(args, rng, sample=args.n > 1) for _ in range(args.n)]
        if args.json:
            rows = [generate(p).to_dict() for p in params]
            print(json.dumps(rows[0] if len(rows) == 1 else rows, ensure_ascii=False, indent=2))
        else:
            for index, p in enumerate(params):
                emit(generate(p), trace=args.trace, qa=args.qa,
                     header=f"\n### Story {index + 1}\n" if len(params) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
