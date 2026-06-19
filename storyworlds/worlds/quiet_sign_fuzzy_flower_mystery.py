#!/usr/bin/env python3
"""A mystery about a quiet sign, a fuzzy flower, and brave reconciliation."""

from __future__ import annotations

import argparse
import copy
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class Garden:
    id: str
    name: str
    silence: str
    confusion: int


@dataclass(frozen=True)
class Sign:
    id: str
    name: str
    message: str
    clue: str


@dataclass(frozen=True)
class Flower:
    id: str
    name: str
    texture: str
    memory: str


@dataclass(frozen=True)
class Friend:
    id: str
    name: str
    hurt: str
    trust: int


@dataclass(frozen=True)
class BraveAct:
    id: str
    name: str
    dialogue: str
    repairs: str
    courage: int


@dataclass(frozen=True)
class Params:
    garden: str
    sign: str
    flower: str
    friend: str
    brave_act: str


@dataclass
class Entity:
    id: str
    name: str
    kind: str
    memes: dict[str, int] = field(default_factory=dict)


@dataclass
class Event:
    id: str
    text: str
    actor: str
    target: str | None = None
    delta: dict[str, int] = field(default_factory=dict)


@dataclass
class MysteryWorld:
    params: Params
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    facts: dict[str, str | int | bool] = field(default_factory=dict)
    meters: dict[str, int] = field(
        default_factory=lambda: {"confusion": 0, "clues": 0, "courage": 0, "trust": 0, "peace": 0}
    )

    def add_entity(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def record(
        self,
        event_id: str,
        text: str,
        actor: str,
        target: str | None = None,
        **delta: int,
    ) -> None:
        self.history.append(Event(event_id, text, actor, target, dict(delta)))
        for key, value in delta.items():
            self.meters[key] = self.meters.get(key, 0) + value


GARDENS = {
    "gate": Garden("gate", "the locked garden gate", "no bird sang near the path", 2),
    "greenhouse": Garden("greenhouse", "the moonlit greenhouse", "every pane held its breath", 1),
    "courtyard": Garden("courtyard", "the stone courtyard", "footsteps sounded smaller than they should", 3),
}

SIGNS = {
    "arrow": Sign("arrow", "quiet arrow sign", "This way only if you mean it", "direction"),
    "sorry": Sign("sorry", "quiet apology sign", "Say the missing sorry aloud", "apology"),
    "name": Sign("name", "quiet name sign", "Remember who planted this", "memory"),
}

FLOWERS = {
    "moss": Flower("moss", "fuzzy moss flower", "soft as a kitten's ear", "heard the apology before it was hidden"),
    "thistle": Flower("thistle", "fuzzy thistle flower", "bristly under its silver fluff", "saw two friends turn away at once"),
    "star": Flower("star", "fuzzy star flower", "powdered with pale blue fuzz", "kept the planter's forgotten name"),
}

FRIENDS = {
    "lena": Friend("lena", "Lena", "thought the secret path was hidden on purpose", 1),
    "milo": Friend("milo", "Milo", "believed his note had been ignored", 1),
    "tess": Friend("tess", "Tess", "felt blamed for breaking the garden latch", 0),
}

BRAVE_ACTS = {
    "ask": BraveAct("ask", "ask the hard question", "\"Tell me what hurt before I guess.\"", "memory", 2),
    "apologize": BraveAct("apologize", "say the first apology", "\"I am sorry I let the sign speak for me.\"", "apology", 3),
    "lead": BraveAct("lead", "lead both friends to the sign", "\"Come with me; I will not solve this alone.\"", "direction", 2),
}


def clue_phrase(clue: str) -> str:
    return {
        "direction": "choosing the path together",
        "apology": "a real apology",
        "memory": "remembering who mattered",
    }.get(clue, clue)


def valid_params(params: Params) -> tuple[bool, str]:
    if params.garden not in GARDENS:
        return False, f"unknown garden: {params.garden}"
    if params.sign not in SIGNS:
        return False, f"unknown sign: {params.sign}"
    if params.flower not in FLOWERS:
        return False, f"unknown flower: {params.flower}"
    if params.friend not in FRIENDS:
        return False, f"unknown friend: {params.friend}"
    if params.brave_act not in BRAVE_ACTS:
        return False, f"unknown brave act: {params.brave_act}"
    if params.garden == "courtyard" and params.flower == "moss":
        return False, "the fuzzy moss flower cannot grow on the dry stone courtyard"
    if params.sign == "arrow" and params.brave_act == "apologize":
        return False, "the arrow sign needs shared direction before apology can solve it"
    if params.friend == "tess" and params.brave_act == "lead":
        return False, "Tess will not follow until someone asks what really happened"
    return True, ""


def all_params() -> list[Params]:
    return [
        Params(garden, sign, flower, friend, brave_act)
        for garden in GARDENS
        for sign in SIGNS
        for flower in FLOWERS
        for friend in FRIENDS
        for brave_act in BRAVE_ACTS
        if valid_params(Params(garden, sign, flower, friend, brave_act))[0]
    ]


def make_world(params: Params) -> MysteryWorld:
    garden = GARDENS[params.garden]
    sign = SIGNS[params.sign]
    flower = FLOWERS[params.flower]
    friend = FRIENDS[params.friend]
    world = MysteryWorld(params)
    world.add_entity(Entity("detective", "Nia", "child detective", {"Brave": 1, "Curiosity": 2}))
    world.add_entity(Entity("sign", sign.name, "physical", {"Quiet": 2, "Clue": 1}))
    world.add_entity(Entity("flower", flower.name, "physical", {"Memory": 2}))
    world.add_entity(Entity("friend", friend.name, "person", {"Hurt": 2, "Trust": friend.trust}))
    world.add_entity(Entity("garden", garden.name, "place", {"Confusion": garden.confusion}))
    world.facts["sign_message"] = sign.message
    world.facts["sign_clue"] = sign.clue
    world.facts["flower_memory"] = flower.memory
    world.facts["hurt"] = friend.hurt
    return world


def enter_garden(world: MysteryWorld) -> None:
    garden = GARDENS[world.params.garden]
    world.record(
        "enter",
        f"Nia entered {garden.name}, where {garden.silence}.",
        "detective",
        "garden",
        confusion=garden.confusion,
    )


def read_sign(world: MysteryWorld) -> None:
    sign = SIGNS[world.params.sign]
    world.record(
        "sign",
        f"The {sign.name} stayed quiet except for one line: \"{sign.message}.\"",
        "sign",
        "detective",
        clues=1,
    )


def ask_flower(world: MysteryWorld) -> None:
    flower = FLOWERS[world.params.flower]
    world.record(
        "flower",
        f"The {flower.name}, {flower.texture}, trembled and remembered that it {flower.memory}.",
        "flower",
        "detective",
        clues=2,
    )


def hear_friend(world: MysteryWorld) -> None:
    friend = FRIENDS[world.params.friend]
    world.record(
        "friend",
        f"{friend.name} whispered, \"I stayed away because I {friend.hurt}.\"",
        "friend",
        "detective",
        trust=friend.trust,
    )


def predict_reconciliation(world: MysteryWorld) -> str:
    imagined = copy.deepcopy(world)
    act = BRAVE_ACTS[imagined.params.brave_act]
    aligned = act.repairs == imagined.facts["sign_clue"]
    imagined.meters["courage"] += act.courage
    imagined.meters["peace"] += 2 if aligned else 1
    if imagined.meters["clues"] + imagined.meters["courage"] + imagined.meters["peace"] >= imagined.meters["confusion"] + 5 and aligned:
        return "Nia saw that the brave answer was not a dramatic accusation, but a conversation that repaired the clue."
    return "Nia saw that bravery without the right kind of listening would leave the sign quiet."


def choose_brave_act(world: MysteryWorld) -> None:
    act = BRAVE_ACTS[world.params.brave_act]
    aligned = act.repairs == world.facts["sign_clue"]
    world.record(
        "dialogue",
        f"Nia chose to {act.name}. She said, {act.dialogue}",
        "detective",
        "friend",
        courage=act.courage,
        peace=2 if aligned else 1,
        trust=1 if aligned else 0,
    )
    world.facts["dialogue"] = act.dialogue
    world.facts["aligned"] = aligned


def resolve_case(world: MysteryWorld) -> None:
    solved = (
        world.meters["clues"] >= 3
        and world.meters["courage"] >= 2
        and world.meters["peace"] >= 2
        and bool(world.facts["aligned"])
    )
    if solved:
        world.record(
            "reconciliation",
            f"The mystery ended in reconciliation because the quiet sign had been asking for {world.facts['sign_clue']}.",
            "sign",
            "friend",
            peace=1,
        )
        world.facts["ending"] = "reconciled"
    else:
        world.record(
            "unsettled",
            "The sign softened, but the fuzzy flower kept one petal curled around the unsolved truth.",
            "flower",
            "detective",
        )
        world.facts["ending"] = "partial"
    world.entities["detective"].memes["Brave"] = world.meters["courage"]
    world.entities["friend"].memes["Trust"] = world.meters["trust"]


def render_story(world: MysteryWorld, prediction: str) -> str:
    lines = [
        "Nia was brave enough to call herself a detective, but the quietest cases had taught her to listen before she solved.",
        world.history[0].text,
        world.history[1].text,
        world.history[2].text,
        world.history[3].text,
        prediction,
        world.history[4].text,
        world.history[5].text,
    ]
    if world.facts["ending"] == "reconciled":
        lines.append("Afterward, the quiet sign stayed quiet, and the friends walked out together past the fuzzy flower.")
    else:
        lines.append("Afterward, Nia stayed beside the flower, brave enough to let the next question be softer.")
    return "\n".join(lines)


def generate(params: Params) -> StorySample:
    ok, reason = valid_params(params)
    if not ok:
        raise StoryError(reason)
    world = make_world(params)
    enter_garden(world)
    read_sign(world)
    ask_flower(world)
    hear_friend(world)
    prediction = predict_reconciliation(world)
    world.facts["prediction"] = prediction
    choose_brave_act(world)
    resolve_case(world)
    story = render_story(world, prediction)
    prompts = [
        "Write a mystery with a quiet sign, a fuzzy flower, and someone brave.",
        "Use dialogue to move the mystery toward reconciliation.",
        "Make the ending depend on simulated clue alignment and trust.",
    ]
    story_qa = [
        QAItem(
            "What did the quiet sign reveal?",
            f"The quiet sign revealed: {world.facts['sign_message']}. "
            f"That message pointed Nia toward {clue_phrase(str(world.facts['sign_clue']))}, which was the kind of repair the friendship needed.",
        ),
        QAItem(
            "How did dialogue affect reconciliation?",
            f"Nia said, {world.facts['dialogue']} "
            + (
                "That matched what the sign was asking for, so the friends could reconcile."
                if world.facts["aligned"]
                else "That was brave, but it was not the repair the sign was asking for, so the mystery stayed partly open."
            ),
        ),
    ]
    world_qa = [
        QAItem(
            "Was the mystery reconciled?",
            (
                "Yes. Nia chose the brave act that matched the sign, and the friends no longer needed the sign to speak for them."
                if world.facts["ending"] == "reconciled"
                else "Not yet. Nia had clues and courage, but the chosen words did not answer the sign's real request."
            ),
        ),
        QAItem(
            "What did the fuzzy flower remember?",
            f"The flower remembered that it {world.facts['flower_memory']}. "
            "Its memory gave Nia something real to listen to before she chose what to say.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def atom(value: str) -> str:
    return value.replace("-", "_")


def asp_program() -> str:
    facts = []
    for key in GARDENS:
        facts.append(f"garden({atom(key)}).")
    for key in SIGNS:
        facts.append(f"sign({atom(key)}).")
    for key in FLOWERS:
        facts.append(f"flower({atom(key)}).")
    for key in FRIENDS:
        facts.append(f"friend({atom(key)}).")
    for key in BRAVE_ACTS:
        facts.append(f"brave_act({atom(key)}).")
    return "\n".join(
        [
            *facts,
            "invalid(G,S,F,R,A) :- G=courtyard, F=moss, garden(G), sign(S), flower(F), friend(R), brave_act(A).",
            "invalid(G,S,F,R,A) :- S=arrow, A=apologize, garden(G), sign(S), flower(F), friend(R), brave_act(A).",
            "invalid(G,S,F,R,A) :- R=tess, A=lead, garden(G), sign(S), flower(F), friend(R), brave_act(A).",
            "valid(G,S,F,R,A) :- garden(G), sign(S), flower(F), friend(R), brave_act(A), not invalid(G,S,F,R,A).",
            "#show valid/5.",
        ]
    )


def verify_asp() -> str:
    import asp

    models = asp.solve(asp_program())
    model = models[0] if models and isinstance(models[0], list) else models
    asp_valid = {tuple(str(part) for part in item) for item in asp.atoms(model, "valid")}
    py_valid = {(p.garden, p.sign, p.flower, p.friend, p.brave_act) for p in all_params()}
    if asp_valid != py_valid:
        missing = sorted(py_valid - asp_valid)
        extra = sorted(asp_valid - py_valid)
        raise StoryError(f"ASP mismatch; missing={missing[:5]} extra={extra[:5]}")
    return f"OK: Python and ASP agree on {len(py_valid)} valid quiet-sign mysteries."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--garden", choices=sorted(GARDENS))
    parser.add_argument("--sign", choices=sorted(SIGNS))
    parser.add_argument("--flower", choices=sorted(FLOWERS))
    parser.add_argument("--friend", choices=sorted(FRIENDS))
    parser.add_argument("--brave-act", choices=sorted(BRAVE_ACTS), dest="brave_act")
    parser.add_argument("--seed", type=int, default=31)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None) -> Params:
    rng = rng or random.Random(args.seed)
    explicit = any(
        value is not None
        for value in (args.garden, args.sign, args.flower, args.friend, args.brave_act)
    )
    if explicit:
        params = Params(
            garden=args.garden or rng.choice(list(GARDENS)),
            sign=args.sign or rng.choice(list(SIGNS)),
            flower=args.flower or rng.choice(list(FLOWERS)),
            friend=args.friend or rng.choice(list(FRIENDS)),
            brave_act=args.brave_act or rng.choice(list(BRAVE_ACTS)),
        )
        ok, reason = valid_params(params)
        if not ok:
            raise StoryError(reason)
        return params
    return rng.choice(all_params())


def iter_samples(args: argparse.Namespace) -> Iterable[StorySample]:
    if args.all:
        for params in all_params():
            yield generate(params)
        return
    rng = random.Random(args.seed)
    for _ in range(max(1, args.n)):
        yield generate(resolve_params(args, rng))


def emit(sample: StorySample, args: argparse.Namespace) -> None:
    if args.json:
        print(sample.to_json())
        return
    print(sample.story)
    if args.trace:
        print("\nTrace:")
        for event in sample.world.history:
            print(f"- {event.id}: {event.text} {event.delta}")
    if args.qa:
        print("\nStory QA:")
        for qa in sample.story_qa:
            print(f"Q: {qa.question}")
            print(f"A: {qa.answer}")
        print("\nWorld QA:")
        for qa in sample.world_qa:
            print(f"Q: {qa.question}")
            print(f"A: {qa.answer}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify_asp())
            return 0
        if args.asp:
            import asp

            print(asp.solve(asp_program()))
            return 0
        for index, sample in enumerate(iter_samples(args)):
            if index:
                print("\n---\n")
            emit(sample, args)
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
