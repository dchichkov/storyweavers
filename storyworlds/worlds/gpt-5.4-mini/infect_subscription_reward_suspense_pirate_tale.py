#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/infect_subscription_reward_suspense_pirate_tale.py
===================================================================================

A standalone storyworld for a tiny pirate-tale domain with a suspense beat:
a child pirate crew signs up for a treasure subscription, one tempting choice
spreads a bad "infecting" whisper through the ship, and a careful captain
restores order by using the right reward at the right time.

This world is built to be small, classical, and simulation-driven:
typed entities, accumulating physical meters and emotional memes, a causal
forward-chaining world model, a reasonableness gate, an ASP twin, and grounded
Q&A.

The seed words are woven into the domain as:
- infect: a rumor / bad choice can infect the crew's mood and plans
- subscription: a treasure-map subscription with regular deliveries
- reward: a prize that motivates safer choices

The style is pirate tale, with suspense in the middle and a concrete ending
image proving what changed.
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

# Make the shared result containers importable when run directly from the repo.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SUSPENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class StoryWorld:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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

    def copy(self) -> "StoryWorld":
        clone = StoryWorld()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[StoryWorld], list[str]]


@dataclass
class Ship:
    id: str
    name: str
    place: str
    suspense: str
    crew_holds: str


@dataclass
class Subscription:
    id: str
    label: str
    delivery: str
    arrives_with: str
    unsafe_hint: str
    safe_hint: str
    makes_rumor: bool = False


@dataclass
class Reward:
    id: str
    label: str
    phrase: str
    shine: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Trouble:
    id: str
    label: str
    smell: str
    spreads: str
    infects: str
    menace: int
    tags: set[str] = field(default_factory=set)


def _r_rumor_spread(world: StoryWorld) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["rumor"] < THRESHOLD:
            continue
        sig = ("rumor_spread", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for crew in world.entities.values():
            if crew.role in {"captain", "mate"}:
                crew.memes["unease"] += 1
        if "deck" in world.entities:
            world.get("deck").meters["tense"] += 1
        out.append("__suspense__")
    return out


def _r_infect_choice(world: StoryWorld) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["infected"] < THRESHOLD:
            continue
        sig = ("infect_choice", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["shame"] += 1
        if "crew" in world.entities:
            world.get("crew").meters["discord"] += 1
        out.append("__infect__")
    return out


def propagate(world: StoryWorld, narrate: bool = True) -> list[str]:
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


CAUSAL_RULES: list[Rule] = [
    Rule("rumor_spread", "social", _r_rumor_spread),
    Rule("infect_choice", "social", _r_infect_choice),
]


def suspense_gate(sub: Subscription, trouble: Trouble, reward: Reward) -> bool:
    return sub.makes_rumor and trouble.menace >= SUSPENSE_MIN and reward.label != trouble.label


def reasoned_reward(world: StoryWorld, reward: Reward) -> bool:
    return reward.id in REWARD_ORDER


def _do_infect(world: StoryWorld, trouble: Trouble, target: Entity, narrate: bool = True) -> None:
    target.meters["infected"] += 1
    target.meters["rumor"] += 1
    propagate(world, narrate=narrate)


def setup(world: StoryWorld, cap: Entity, mate: Entity, ship: Ship, sub: Subscription) -> None:
    cap.memes["duty"] += 1
    mate.memes["curiosity"] += 1
    world.say(
        f"The ship {ship.name} rocked under a gray sky, and the crew kept one eye "
        f"on the dark water. {cap.id} and {mate.id} had just signed up for "
        f"{sub.label}, hoping the next delivery would lead to treasure."
    )
    world.say(
        f"{ship.suspense} The lantern light swung slow, and every creak of the deck "
        f"sounded like a secret."
    )


def promise(world: StoryWorld, cap: Entity, mate: Entity, sub: Subscription, reward: Reward) -> None:
    world.say(
        f"Each week, the {sub.label} brought a fresh clue in a sealed shell, and "
        f"the promise of {reward.phrase} if the crew kept the trail in order."
    )


def need_and_tempt(world: StoryWorld, cap: Entity, mate: Entity, trouble: Trouble, sub: Subscription) -> None:
    world.say(
        f"But the clue box sat shut, and the captain heard a whisper that the "
        f"sealed wax might {trouble.infect} the message if it was opened too soon."
    )
    world.say(
        f'{mate.id} bit {mate.pronoun("possessive")} lip. "If we wait, we might miss '
        f"the next delivery," {mate.pronoun()} said."
    )


def warn(world: StoryWorld, cap: Entity, mate: Entity, trouble: Trouble, reward: Reward) -> None:
    cap.memes["caution"] += 1
    world.say(
        f'{cap.id} held up a hand. "No rush. A bad choice can {trouble.infect} the '
        f'whole deck, and then we would lose the {reward.label} for the day."'
    )


def defy(world: StoryWorld, mate: Entity, trouble: Trouble, sub: Subscription) -> None:
    mate.memes["defiance"] += 1
    world.say(
        f'{mate.id} frowned, then pried the seal anyway. "I only want to peek," '
        f'{mate.id} muttered.'
    )


def infect(world: StoryWorld, trouble: Trouble, target: Entity) -> None:
    _do_infect(world, trouble, target)
    world.say(
        f"The seal split with a soft crack, and a sour little rumor spread like a "
        f"stain through the crew. It was not a true curse, but it acted like one: "
        f"it {trouble.spreads} from hand to hand, and the room grew tense."
    )


def alarm(world: StoryWorld, cap: Entity, mate: Entity, trouble: Trouble) -> None:
    world.say(
        f'"{mate.id}!" {cap.id} cried. "That whisper can {trouble.infect} the whole '
        f"plan if we let it grow!""
    )


def rescue(world: StoryWorld, cap: Entity, trouble: Trouble, reward: Reward) -> None:
    world.get("deck").meters["tense"] = 0.0
    world.get("crew").meters["discord"] = 0.0
    cap.memes["relief"] += 1
    world.say(
        f"The captain snapped the seal shut, swept the rumor overboard, and doused "
        f"the worry with calm words. The deck loosened at once, like a rope after a knot."
    )
    world.say(
        f'By lantern glow, the crew remembered the {reward.label}, and the path "
        f"ahead looked safe again.'
    )


def lesson(world: StoryWorld, cap: Entity, mate: Entity, sub: Subscription, reward: Reward) -> None:
    cap.memes["care"] += 1
    mate.memes["lesson"] += 1
    world.say(
        f'"If a thing can infect the whole ship with trouble," {cap.id} said softly, '
        f'"we do not chase it alone. We call for help, slow down, and keep the "
        f"subscription box sealed until the right time."'
    )
    world.say(
        f'{mate.id} nodded and tucked the shell away. "I want the reward, but I '
        f"want a safe ship more," {mate.id} said."
    )


def safe_turn(world: StoryWorld, cap: Entity, mate: Entity, reward: Reward, sub: Subscription) -> None:
    cap.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"The next morning, the {sub.label} arrived clean and bright. This time the "
        f"crew opened it together, and inside was {reward.phrase}, shining like a coin "
        f"found at the bottom of a calm sea."
    )
    world.say(
        f"{cap.id} and {mate.id} grinned as the ship slid onward, quiet and ready "
        f"for the next clue."
    )


def tell(ship: Ship, sub: Subscription, reward: Reward, trouble: Trouble,
         captain: str = "Captain Mira", captain_gender: str = "girl",
         mate: str = "Jack", mate_gender: str = "boy") -> StoryWorld:
    world = StoryWorld()
    cap = world.add(Entity(id=captain, kind="character", type=captain_gender, role="captain"))
    mate_ent = world.add(Entity(id=mate, kind="character", type=mate_gender, role="mate"))
    world.add(Entity(id="deck", type="place", label="the deck"))
    world.add(Entity(id="crew", type="group", label="the crew"))

    setup(world, cap, mate_ent, ship, sub)
    world.para()
    promise(world, cap, mate_ent, sub, reward)
    need_and_tempt(world, cap, mate_ent, trouble, sub)
    warn(world, cap, mate_ent, trouble, reward)

    if not suspense_gate(sub, trouble, reward):
        raise StoryError("This storyworld needs a suspenseful subscription/reward hazard.")

    world.para()
    defy(world, mate_ent, trouble, sub)
    infect(world, trouble, mate_ent)
    alarm(world, cap, mate_ent, trouble)

    world.para()
    rescue(world, cap, trouble, reward)
    lesson(world, cap, mate_ent, sub, reward)
    world.para()
    safe_turn(world, cap, mate_ent, reward, sub)

    world.facts.update(
        captain=cap, mate=mate_ent, ship=ship, subscription=sub,
        reward=reward, trouble=trouble, outcome="contained",
        infected=mate_ent.meters["infected"] >= THRESHOLD,
        tense=world.get("deck").meters["tense"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    ship: str
    subscription: str
    reward: str
    trouble: str
    captain: str
    captain_gender: str
    mate: str
    mate_gender: str
    seed: Optional[int] = None


SHIPS = {
    "gale": Ship("gale", "the Gull's Wake", "the deck", "The lantern light swung slow, and every creak of the deck sounded like a secret.", "the crew"),
    "tide": Ship("tide", "the Tide Runner", "the deck", "A hush sat over the railings, and the sea kept its own counsel.", "the crew"),
    "hook": Ship("hook", "the Hook and Sail", "the deck", "The ropes whispered in the wind, and even the mast seemed to listen.", "the crew"),
}

SUBSCRIPTIONS = {
    "map": Subscription("map", "treasure-map subscription", "deliveries", "a sealed shell", "the clue might infect the plan", "the clue would stay safe", makes_rumor=True),
    "chart": Subscription("chart", "chart subscription", "deliveries", "a wax-sealed bottle", "the wax might infect the message", "the wax keeps the message safe", makes_rumor=True),
    "stamps": Subscription("stamps", "mail-rumor subscription", "deliveries", "a little paper chest", "the rumor might infect the crew's mood", "the chest keeps the paper dry", makes_rumor=True),
}

REWARDS = {
    "coin": Reward("coin", "gold coin", "a gold coin for the winner", "shining", tags={"coin", "reward"}),
    "parrot": Reward("parrot", "parrot feather", "a bright parrot feather as reward", "glowing", tags={"feather", "reward"}),
    "telescope": Reward("telescope", "telescope", "a small brass telescope as reward", "gleaming", tags={"telescope", "reward"}),
}

TROUBLES = {
    "rumor": Trouble("rumor", "rumor", "sour", "spreads from hand to hand", "infect", 2, tags={"infect", "suspense"}),
    "mold": Trouble("mold", "mold", "musty", "spreads through the damp corner", "infect", 3, tags={"infect", "suspense"}),
}

CAPTAIN_NAMES = ["Mira", "Nina", "Rose", "Ava", "Luna"]
MATE_NAMES = ["Jack", "Finn", "Toby", "Eli", "Ben"]

REWARD_ORDER = ["coin", "parrot", "telescope"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for ship in SHIPS:
        for sub in SUBSCRIPTIONS:
            for reward in REWARDS:
                for trouble in TROUBLES:
                    if suspense_gate(SUBSCRIPTIONS[sub], TROUBLES[trouble], REWARDS[reward]):
                        combos.append((ship, sub, reward, trouble))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate suspense world with subscription, reward, and infect.")
    ap.add_argument("--ship", choices=SHIPS)
    ap.add_argument("--subscription", choices=SUBSCRIPTIONS)
    ap.add_argument("--reward", choices=REWARDS)
    ap.add_argument("--trouble", choices=TROUBLES)
    ap.add_argument("--captain")
    ap.add_argument("--captain-gender", choices=["girl", "boy"])
    ap.add_argument("--mate")
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
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
              if (args.ship is None or c[0] == args.ship)
              and (args.subscription is None or c[1] == args.subscription)
              and (args.reward is None or c[2] == args.reward)
              and (args.trouble is None or c[3] == args.trouble)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    ship, sub, reward, trouble = rng.choice(sorted(combos))
    captain_gender = args.captain_gender or rng.choice(["girl", "boy"])
    mate_gender = args.mate_gender or rng.choice(["girl", "boy"])
    captain = args.captain or rng.choice(CAPTAIN_NAMES)
    mate = args.mate or rng.choice([n for n in MATE_NAMES if n != captain])
    return StoryParams(ship, sub, reward, trouble, captain, captain_gender, mate, mate_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SHIPS[params.ship], SUBSCRIPTIONS[params.subscription], REWARDS[params.reward], TROUBLES[params.trouble],
                 params.captain, params.captain_gender, params.mate, params.mate_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: StoryWorld) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate suspense story that includes the words "subscription", "reward", and "infect".',
        f"Tell a short pirate tale where {f['captain'].id} and {f['mate'].id} wait for a subscription delivery, face a tense moment, and end with a reward.",
        f"Write a suspenseful sea story for a young child where a bad choice might infect the crew's plan, but the captain saves the day.",
    ]


def story_qa(world: StoryWorld) -> list[tuple[str, str]]:
    f = world.facts
    cap, mate, sub, reward, trouble = f["captain"], f["mate"], f["subscription"], f["reward"], f["trouble"]
    return [
        ("Who are the main characters?",
         f"The main characters are {cap.id} and {mate.id}, the captain and the mate who were waiting for the next clue."),
        ("What did they subscribe to?",
         f"They subscribed to {sub.label}, which brought a new clue on a regular schedule."),
        ("What was the reward?",
         f"The reward was {reward.phrase}, a bright prize that made the crew want to stay careful."),
        ("What happened when the seal was opened too soon?",
         f"A sour rumor spread and could infect the crew's mood and plan. It made the deck tense until the captain fixed it."),
        ("How did the story end?",
         f"It ended safely, with the crew opening the next delivery together and seeing {reward.phrase} shine in the lantern light."),
    ]


def world_knowledge_qa(world: StoryWorld) -> list[tuple[str, str]]:
    return [
        ("What is a subscription?",
         "A subscription is when something is delivered again and again over time, like a regular box or message."),
        ("What does infect mean in this story?",
         "Here, infect means a bad idea or rumor spreads to other people and changes how they feel or act."),
        ("Why is a reward helpful?",
         "A reward gives the crew a goal to work toward, so they are more likely to wait and choose the safer way."),
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


def dump_trace(world: StoryWorld) -> str:
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
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("gale", "map", "coin", "rumor", "Mira", "girl", "Jack", "boy"),
    StoryParams("tide", "chart", "telescope", "rumor", "Nina", "girl", "Finn", "boy"),
    StoryParams("hook", "stamps", "parrot", "mold", "Rose", "girl", "Toby", "boy"),
]


def explain_rejection(sub: Subscription, trouble: Trouble) -> str:
    return f"(No story: the subscription cannot reasonably let {trouble.infect} happen here.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SHIPS:
        lines.append(asp.fact("ship", sid))
    for sid, s in SUBSCRIPTIONS.items():
        lines.append(asp.fact("subscription", sid))
        if s.makes_rumor:
            lines.append(asp.fact("makes_rumor", sid))
    for rid, r in REWARDS.items():
        lines.append(asp.fact("reward", rid))
    for tid, t in TROUBLES.items():
        lines.append(asp.fact("trouble", tid))
        lines.append(asp.fact("menace", tid, t.menace))
    lines.append(asp.fact("suspense_min", SUSPENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, Sub, R, T) :- ship(S), subscription(Sub), reward(R), trouble(T),
                       makes_rumor(Sub), menace(T, M), suspense_min(N), M >= N.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid combos differ.")
        rc = 1
    else:
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


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
        print(asp_program(show="#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible (ship, subscription, reward, trouble) combos:")
        for row in asp_valid_combos():
            print("  ", row)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def generate_from_args() -> StorySample:
    args = build_parser().parse_args([])
    return generate(resolve_params(args, random.Random(0)))


if __name__ == "__main__":
    main()
