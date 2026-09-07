#!/usr/bin/env python3
"""Decide, Darling: a small dining-room quest about choosing with care.

A child must decide which place setting will welcome a shy new neighbor. The
quest is gentle but suspenseful: a missing blue cup may change the plan.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    label: str
    kind: str = "thing"
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    beliefs: dict[str, str] = field(default_factory=dict)


@dataclass
class Event:
    kind: str
    text: str
    question: str = ""
    cause: str = ""
    result: str = ""
    state: dict = field(default_factory=dict)


@dataclass
class StoryParams:
    hero: str = "Mina"
    darling: str = "Aunt Rose"
    guest: str = "Leo"
    centerpiece: str = "sunflowers"
    worry: str = "missing_cup"
    plan: str = "find_cup"
    seed: int = 777


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities = {
            "hero": Entity("hero", params.hero, "character",
                           memes={"hope": 0.6, "worry": 0.5, "courage": 0.4}),
            "darling": Entity("darling", params.darling, "character",
                              memes={"warmth": 0.9, "patience": 0.9}),
            "guest": Entity("guest", params.guest, "character",
                            memes={"shyness": 0.8, "belonging": 0.2}),
            "table": Entity("table", "the dining table", "furniture",
                            location="dining room",
                            meters={"seats": 3, "set": 0}),
            "cup": Entity("cup", "the blue cup", "dish",
                          location="kitchen shelf",
                          meters={"fragile": 1}),
            "flowers": Entity("flowers", f"the {params.centerpiece}", "centerpiece",
                              location="garden",
                              meters={"stems": 5}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question: str = "",
                cause: str = "", result: str = ""):
        self.history.append(Event(kind, text, question, cause, result,
                                  self.snapshot()))

    def speak(self, speaker: str, text: str, *, listener: str = ""):
        if speaker not in self.entities:
            raise StoryError("A story speaker must be a known character.")
        if not text or not text.strip():
            raise StoryError("A spoken line cannot be empty.")
        label = self.entities[speaker].label
        verb = "asked" if text.rstrip().endswith("?") else "said"
        self.history.append(Event(
            "speech", f'"{text}" {label} {verb}.',
            state=self.snapshot(),
        ))

    def sample(self) -> StorySample:
        return StorySample(
            params=self.params,
            story="\n\n".join(event.text for event in self.history),
            prompts=[PROMPT],
            story_qa=[
                QAItem(event.question, f"{event.cause} {event.result}")
                for event in self.history if event.question
            ],
            world_qa=[
                QAItem("Where did the quest happen?",
                       "The quest happened in the dining room."),
                QAItem("Why was the blue cup important?",
                       "It was Leo's familiar cup, so it could help him feel at home.")
            ],
            world=self,
        )


NAMES = ("Mina", "Nora", "Pip", "Theo", "June", "Ari")
DARLINGS = ("Aunt Rose", "Grandma May", "Uncle Sol")
GUESTS = ("Leo", "Nia", "Sam", "Ivy")
FLOWERS = ("sunflowers", "daisies", "marigolds")
WORRIES = ("missing_cup", "wobbly_chair")

PROMPT = (
    "Write a heartwarming, dialogue-rich children's story in a dining room "
    "where a child must decide how to welcome a shy guest."
)

ASP_RULES = """
welcome_plan(missing_cup,find_cup).
welcome_plan(missing_cup,borrow_cup).
welcome_plan(wobbly_chair,move_chair).
valid(W,P) :- worry(W), plan(P), welcome_plan(W,P).
#show valid/2.
"""

PLANS = {
    "missing_cup": ("find_cup", "borrow_cup"),
    "wobbly_chair": ("move_chair",),
}


def valid_combos() -> list[tuple[str, str]]:
    return [(worry, plan) for worry, plans in PLANS.items() for plan in plans]


def validate_params(params: StoryParams):
    if (params.worry, params.plan) not in valid_combos():
        raise StoryError("That plan does not solve the selected dining-room worry.")
    if params.worry not in PLANS:
        raise StoryError("Unknown dining-room worry.")
    if params.worry == "missing_cup" and params.seed < 0:
        raise StoryError("The cup quest needs a nonnegative story seed.")
    if params.hero == params.guest:
        raise StoryError("The planner and guest need different names.")
    if params.hero == params.darling:
        raise StoryError("The planner and darling need different names.")
    if params.guest == params.darling:
        raise StoryError("The guest and darling need different names.")
    for name in (params.hero, params.guest):
        if not re.fullmatch(r"[A-Z][a-z]+", name):
            raise StoryError("Use simple capitalized names for child characters.")
    if not re.fullmatch(r"(Aunt|Grandma|Uncle) [A-Z][a-z]+", params.darling):
        raise StoryError("The darling's name should be a simple family title and name.")
    if params.centerpiece not in FLOWERS:
        raise StoryError("Choose a registered flower centerpiece.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    world.entities["chair"] = Entity(
        "chair", "the little chair", "furniture", location="dining room",
        meters={"steady": 0 if params.worry == "wobbly_chair" else 1})
    return world


def complete_quest(world: World):
    p = world.params
    table = world.entities["table"]
    guest = world.entities["guest"]
    cup = world.entities["cup"]
    chair = world.entities["chair"]
    if table.meters["set"] != 3:
        raise StoryError("All three places must be set before the supper begins.")
    if guest.memes["belonging"] < 1:
        raise StoryError("The guest must be shown a real welcome.")
    if p.worry == "missing_cup" and cup.location != "table":
        raise StoryError("The chosen cup must actually reach the table.")
    if p.worry == "wobbly_chair" and chair.meters["steady"] != 1:
        raise StoryError("The chair must be made steady before anyone sits.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    p = params
    h = p.hero
    d = p.darling
    g = p.guest
    table = world.entities["table"]
    cup = world.entities["cup"]
    flowers = world.entities["flowers"]
    guest = world.entities["guest"]
    chair = world.entities["chair"]

    world.narrate(
        "beginning",
        f"In the dining room, {h} arranged three plates beneath a bright bowl of "
        f"{p.centerpiece}. {d} was stirring soup, and {g} was due at the door for supper."
    )
    world.speak("hero", f"{d}, I want {g} to feel at home.")
    world.speak("darling", f"Then decide, darling. What might help him feel safe?")
    world.speak("hero", "I could choose the blue cup. He told me it is his favorite.")
    world.speak("darling", "A thoughtful choice is a small bridge.")

    world.narrate(
        "inner_monologue",
        f"{h} looked at the empty place beside the flowers. "
        f"Inside, a worried thought fluttered: What if my choice was not enough?"
    )

    if p.worry == "missing_cup":
        world.speak("hero", "The blue cup is gone!")
        world.speak("darling", "We can borrow another cup, or we can look carefully.")
        world.narrate(
            "suspense",
            f"The front bell jingled once. {g} would arrive soon, but the blue cup "
            f"was not on the kitchen shelf.",
            question="Why did the missing cup make the dining-room quest suspenseful?",
            cause="Leo was about to arrive, and his familiar blue cup could help him feel safe.",
            result="Mina had to decide quickly whether to search or borrow another cup."
        )
        if p.plan == "find_cup":
            world.speak("hero", "I will look in the places we really used it.")
            world.speak("darling", "Good deciding. I will check the dish rack.")
            world.narrate(
                "search",
                f"{h} remembered carrying the cup after breakfast. "
                f"She searched beside the window, under a folded napkin, and behind the bread box."
            )
            cup.location = "pantry"
            world.narrate(
                "turn",
                f"At last, {h} heard a tiny clink. The blue cup was tucked in the pantry "
                f"beside the picnic basket.",
                question="How did Mina find the blue cup?",
                cause="She remembered where it had been carried after breakfast and searched carefully.",
                result="She found it in the pantry beside the picnic basket."
            )
            world.speak("hero", "There you are! I decided to keep looking because this cup matters to Leo.")
        else:
            world.speak("hero", "I will borrow a cup, so Leo does not wait alone.")
            world.speak("darling", "That is kind. We can keep searching while the kettle sings.")
            borrowed = Entity("borrowed", "the yellow cup", "dish", location="table")
            world.entities["borrowed"] = borrowed
            world.narrate(
                "turn",
                f"{d} placed a sunny yellow cup at the empty place while {h} kept the blue "
                f"cup's place ready.",
                question="Why did Mina borrow a different cup?",
                cause="Leo was arriving soon, and waiting for the missing cup could make the welcome feel rushed.",
                result="A yellow cup made a ready place while the family continued looking."
            )
            world.speak("hero", "The yellow cup is ready, but I will still find the blue one.")
            world.speak("darling", "A welcome can have a careful plan and a patient heart.")
            cup.location = "pantry"
            world.narrate(
                "search",
                f"Behind the bread box, {h} found the blue cup. She washed it and set it beside the yellow cup."
            )
        cup.location = "table"
        world.narrate("return_cup", f"{h} set the blue cup at {g}'s place at the dining table.")
    else:
        world.speak("hero", "The little chair wiggles when I touch it.")
        world.speak("darling", "Then decide whether to risk it or find a kinder seat.")
        world.narrate(
            "suspense",
            f"The chair gave a soft creak just as footsteps sounded outside. "
            f"{g} would be at the dining room door in moments.",
            question="Why did the wobbly chair matter before supper?",
            cause="A shaky seat could make a shy guest feel unsafe during his first visit.",
            result="Mina had to choose a steadier place before Leo arrived."
        )
        world.speak("hero", "I will move the sturdy chair near the flowers.")
        world.speak("darling", "A wise choice, darling. Leave the wobbly one for no one.")
        chair.location = "hall"
        chair.meters["steady"] = 1
        world.narrate(
            "turn",
            f"{h} carried the sturdy chair into the dining room and pushed it close to "
            f"the warm pool of lamplight.",
            question="How did Mina make the dining room safer?",
            cause="She noticed that the little chair wobbled when touched.",
            result="She moved a sturdy chair near the flowers and kept the wobbly one away."
        )
        world.speak("hero", "Now Leo can see everyone, and everyone can see him.")
        world.speak("darling", "That is a place made with care.")

    flowers.location = "table"
    table.meters["set"] = 3
    guest.memes["belonging"] = 1
    world.narrate(
        "welcome",
        f"The bell rang again. {g} stepped into the dining room and saw a place waiting "
        f"near the {p.centerpiece}. {h} pulled out the chair.",
        question="What showed Leo that the family had planned for him?",
        cause="Mina and {d} prepared a place with a thoughtful cup, steady seat, and flowers."
        .format(d=d),
        result="Leo saw a ready chair and a welcoming place at the dining table."
    )
    world.speak("guest", "You remembered me.")
    world.speak("hero", "We did. Will you sit beside me?")
    world.speak("darling", "There is always room at this table.")
    world.narrate(
        "ending",
        f"Leo smiled and sat down. The soup steamed, the {p.centerpiece} glowed in the "
        f"lamplight, and {h} felt the flutter inside become a warm, quiet yes."
    )

    complete_quest(world)
    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample):
    world = sample.world
    complete_quest(world)
    speech = [e for e in world.history if e.kind == "speech"]
    if len(speech) < 12:
        raise StoryError("The story needs a sustained back-and-forth conversation.")
    if not any("decide" in e.text.lower() for e in speech):
        raise StoryError("The dialogue must include the deciding moment.")
    if not any(e.kind == "inner_monologue" for e in world.history):
        raise StoryError("The story needs an inner-monologue moment.")
    if not any(e.kind == "suspense" for e in world.history):
        raise StoryError("The story needs a suspense turn.")
    if len(sample.story_qa) < 3:
        raise StoryError("The story needs several causal grounded questions.")
    if any("{" in item.answer or "}" in item.answer for item in sample.story_qa):
        raise StoryError("Child-facing answers must not contain template fields.")


def asp_facts() -> str:
    from asp import fact
    facts = []
    for worry, plans in PLANS.items():
        facts.append(fact("worry", worry))
        for plan in plans:
            facts.append(fact("plan", plan))
    for worry, plan in valid_combos():
        facts.append(fact("welcome_plan", worry, plan))
    return "\n".join(facts)


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "valid"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--darling")
    parser.add_argument("--guest")
    parser.add_argument("--centerpiece", choices=FLOWERS)
    parser.add_argument("--worry", choices=WORRIES)
    parser.add_argument("--plan", choices=("find_cup", "borrow_cup", "move_chair"))
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        (worry, plan) for worry, plan in valid_combos()
        if (args.worry is None or worry == args.worry)
        and (args.plan is None or plan == args.plan)
    ]
    if not choices:
        raise StoryError("That plan does not solve the selected dining-room worry.")
    worry, plan = rng.choice(choices)
    hero = args.hero or rng.choice(NAMES)
    darling = args.darling or rng.choice([x for x in DARLINGS if x != hero])
    guest = args.guest or rng.choice([x for x in GUESTS if x != hero])
    params = StoryParams(
        hero=hero,
        darling=darling,
        guest=guest,
        centerpiece=args.centerpiece or rng.choice(FLOWERS),
        worry=worry,
        plan=plan,
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify():
    if set(valid_combos()) != asp_combos():
        raise StoryError("Python and ASP disagree about valid dining-room plans.")
    tested = 0
    for worry, plan in valid_combos():
        params = StoryParams(worry=worry, plan=plan, seed=777)
        generate(params)
        tested += 1
    print(f"OK: {tested} story states; {len(valid_combos())} Python/ASP-compatible plans.")


def emit(sample: StorySample, *, trace=False, qa=False, header=""):
    if header:
        print(header)
    print(sample.story)
    if qa:
        for item in sample.story_qa:
            print(f"\nQ: {item.question}\nA: {item.answer}")
    if trace:
        print("\nTRACE")
        print(json.dumps({
            "entities": sample.world.snapshot(),
            "history": [asdict(event) for event in sample.world.history],
        }, indent=2))


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
            params_list = []
            for worry, plan in valid_combos():
                if args.worry and args.worry != worry:
                    continue
                if args.plan and args.plan != plan:
                    continue
                local = argparse.Namespace(**vars(args))
                local.worry = worry
                local.plan = plan
                params_list.append(resolve_params(local, rng))
            if not params_list:
                raise StoryError("No valid plans match these options.")
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]
        samples = [generate(params) for params in params_list]
        if args.json:
            data = [sample.to_dict() for sample in samples]
            print(json.dumps(data[0] if len(data) == 1 else data,
                             ensure_ascii=False, indent=2))
        else:
            for index, sample in enumerate(samples):
                emit(sample, trace=args.trace, qa=args.qa,
                     header=(f"\n### Story {index + 1}\n"
                             if len(samples) > 1 else ""))
        return 0
    except StoryError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
