#!/usr/bin/env python3
"""
A standalone Storyweavers world: a gentle superhero quest about ending a grizzly
problem by searching carefully and listening to an inner voice.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "storyworlds", "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


THEME = "superhero story"
SEED_WORDS = {"terminate", "grizzly", "scour"}


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def __post_init__(self) -> None:
        for key in ("danger", "energy", "mess", "distance"):
            self.meters.setdefault(key, 0.0)
        for key in ("courage", "worry", "trust", "joy", "curiosity"):
            self.memes.setdefault(key, 0.0)


@dataclass
class StoryParams:
    hero: str = "Luna"
    partner: str = "Max"
    grizzly: str = "Brumble"
    quest: int = 0
    voice: int = 0
    ending: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Quest:
    place: str
    threat: str
    clue: str
    false_lead: str
    thought: str
    tool: str
    discovery: str
    cause: str
    repair: str
    proof: str
    lesson: str
    ending: str


QUESTS = [
    Quest(
        place="Moonbeam Park",
        threat="a grizzly shadow-machine had covered the playground in noisy darkness",
        clue="small silver pawprints leading from the shadow-machine to the old lighthouse",
        false_lead="a windy banner flapping over the snack stand",
        thought="The banner is loud, but the silver pawprints show where the trouble traveled.",
        tool="the hand-crank sun lantern",
        discovery="found the grizzly shadow-machine wedged beneath the lighthouse stairs",
        cause="had pressed the machine's growl button while trying to make a bedtime signal",
        repair="turned the crank slowly, cleaned the lens, and aimed the warm beam at the playground",
        proof="the swings shone clearly while the machine gave only a soft harmless hum",
        lesson="A hero follows evidence and repairs danger instead of rushing to punish someone.",
        ending="Moonbeam Park glowed again, and every swing cast a tiny star-shaped shadow.",
    ),
    Quest(
        place="Cloudtop City",
        threat="a grizzly storm-bot had tangled the city's rescue balloons above the square",
        clue="a strip of blue ribbon caught on the bot's turning claw",
        false_lead="a loose kite dancing above the clock tower",
        thought="The kite is flying away, but the ribbon shows what touched the balloons.",
        tool="the calm-wind rescue fan",
        discovery="reached the storm-bot on the clock tower and freed its jammed claw",
        cause="had grabbed the ribbon to decorate a gift and accidentally pulled the bot's control cable",
        repair="held the balloons steady, untangled the ribbon, and replaced the bent cable",
        proof="the balloons rose in a neat line and the bot waved instead of clanking",
        lesson="A careful rescue can turn a frightening machine into a helpful friend.",
        ending="The rescue balloons formed a bright heart above Cloudtop City.",
    ),
    Quest(
        place="The Glow Tunnel",
        threat="a grizzly tunnel crawler had stopped the train by scattering glowing stones",
        clue="one warm stone tucked inside a crawler wheel",
        false_lead="a trail of glitter disappearing toward the ticket booth",
        thought="Glitter can travel anywhere, but a warm stone inside the wheel explains the stop.",
        tool="the magnetic moon-rope",
        discovery="lifted the crawler gently and removed the glowing stone from its wheel",
        cause="had collected the stones for a den and rolled onto the track before hearing the train bell",
        repair="moved the stones into a safe basket and painted a bright warning line beside the track",
        proof="the train rolled past safely while the crawler watched from behind the line",
        lesson="Strong heroes make a safe path for everyone, even when a mistake caused the trouble.",
        ending="The train's windows blinked like friendly eyes as it carried everyone home.",
    ),
    Quest(
        place="Sunrise Harbor",
        threat="a grizzly tide-cart had blocked the boats with a mountain of floating crates",
        clue="a yellow badge stuck beneath the cart's brake",
        false_lead="a gull carrying a shiny spoon over the water",
        thought="The spoon is shiny, but the badge is trapped where the brake stopped the cart.",
        tool="the bright rescue rope",
        discovery="scoured the dock and found the tide-cart's brake locked under the crates",
        cause="had pulled the cart close to the water while searching for a lost badge",
        repair="unlocked the brake, tied the crates into a safe raft, and cleared the boat lane",
        proof="three boats crossed the harbor without bumping a single crate",
        lesson="Searching carefully means checking both the obvious mess and the hidden cause.",
        ending="At sunrise, the harbor bells rang while the safe raft bobbed beside the dock.",
    ),
    Quest(
        place="Pinecone Valley",
        threat="a grizzly guardian suit had frightened the valley animals away from their garden",
        clue="a torn note inside the suit saying, 'Please help me stop'",
        false_lead="deep footprints circling the cabbage patch",
        thought="The footprints show that the suit moved, but the note tells us someone wants the movement to stop.",
        tool="the quiet key",
        discovery="opened the guardian suit and found its emergency button stuck beneath a pinecone",
        cause="had tested the suit's roar and dropped the pinecone onto its button",
        repair="removed the pinecone, softened the roar, and invited the animals back with fresh vegetables",
        proof="rabbits nibbled safely while the guardian suit stood still beside the gate",
        lesson="Listening to a frightened request can reveal the kindest rescue.",
        ending="The garden filled with happy hops, and the guardian wore a flower crown.",
    ),
]


@dataclass
class World:
    hero: Entity
    partner: Entity
    grizzly: Entity
    signal: Entity
    place: Entity
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def make_entity(
    eid: str,
    kind: str,
    type_: str,
    label: str,
    *,
    location: str = "",
) -> Entity:
    return Entity(id=eid, kind=kind, type=type_, label=label, location=location)


def build_world(params: StoryParams, quest: Quest) -> World:
    hero = make_entity(params.hero, "character", "hero", "the young superhero")
    partner = make_entity(params.partner, "character", "helper", "the trusted partner")
    grizzly = make_entity(params.grizzly, "character", "grizzly", "the grizzly helper")
    signal = make_entity("signal", "thing", "beacon", "the rescue signal")
    place = make_entity("place", "location", "setting", quest.place, location=quest.place)
    return World(hero, partner, grizzly, signal, place)


def tell(params: StoryParams) -> World:
    quest = QUESTS[params.quest % len(QUESTS)]
    world = build_world(params, quest)
    h, p, g = world.hero, world.partner, world.grizzly

    h.memes["courage"] += 1
    h.memes["curiosity"] += 1
    p.memes["trust"] += 1
    g.memes["worry"] += 2
    g.meters["danger"] = 2
    world.signal.meters["energy"] = 0
    world.place.meters["distance"] = 3

    openings = [
        f"In {quest.place}, {h.id} wore a bright cape and watched over the people below.",
        f"The sun was setting over {quest.place} when {h.id} heard a call for help.",
        f"{h.id} and {p.id} were practicing superhero rescues near {quest.place}.",
        f"Every hero needs a quest, and {h.id}'s began when the alarm rang in {quest.place}.",
    ]
    world.say(openings[params.voice % len(openings)])
    world.say(f"A grizzly machine or guardian had caused a new danger: {quest.threat}.")
    world.say(f"{h.id} lifted the rescue signal, but it stayed dark because the safe path was not clear.")

    world.para()
    world.say(f"Near the trouble, the team noticed {quest.clue}.")
    world.say(f"At the same time, {quest.false_lead}.")
    thoughts = [
        quest.thought,
        f"{quest.thought} I will not chase the loudest thing first.",
        f"{quest.thought} The smallest detail may explain the biggest danger.",
        f"{quest.thought} A real rescue begins by asking what each mark can prove.",
    ]
    inner = thoughts[params.voice % len(thoughts)]
    h.memes["curiosity"] += 1
    world.say(f"Inside {h.id}'s mind, an inner monologue whispered, '{inner}'.")

    dialogues = [
        f"'{p.id}, will you check the false lead while I follow the tracks?' {h.id} asked. "
        f"'Yes,' said {p.id}. 'We will compare what we learn.'",
        f"'Should we rush in?' asked {p.id}. 'No,' said {h.id}. 'A superhero protects people by thinking first.'",
        f"{g.id} trembled and said, 'I do not know how to stop this.' "
        f"{h.id} answered, 'Tell us what you touched, and we can help.'",
        f"'The clue points toward the lighthouse,' said {p.id}. "
        f"'Then our quest has a direction,' replied {h.id}.",
    ]
    world.say(dialogues[(params.voice + params.ending) % len(dialogues)])
    world.say(f"Together they carried {quest.tool} toward the safest route.")

    world.para()
    world.say(
        "The first search found only a rattling gate. The false lead explained a sound, "
        "but it did not explain the danger."
    )
    world.say(
        f"{h.id} and {p.id} returned to the stronger clue and {quest.discovery}."
    )
    g.meters["danger"] = 1
    g.memes["worry"] += 1
    world.say(
        f"The grizzly froze. {g.id} said, 'I wanted to help, but I {quest.cause}.'"
    )
    world.say(
        f"{h.id} answered, 'Thank you for telling us. Now we can make the danger stop safely.'"
    )

    world.para()
    world.say(f"The heroes used {quest.tool} and {quest.repair}.")
    g.meters["danger"] = 0
    world.signal.meters["energy"] = 1
    h.memes["courage"] += 2
    p.memes["trust"] += 1
    g.memes["worry"] = 0
    g.memes["joy"] += 2
    world.say(f"They did not simply chase the problem away; they helped terminate the danger at its cause.")
    world.say(f"Then they tested their work: {quest.proof}.")
    world.say(
        f"{p.id} grinned. 'The quest is finished.' {h.id} smiled. "
        f"'A happy ending is safest when everyone can share it.'"
    )
    world.say(f"{quest.lesson}")

    world.para()
    ending_lines = [
        quest.ending,
        f"The rescue signal shone above them. {quest.ending}",
        f"Everyone cheered for the team. {quest.ending}",
        f"{g.id} helped carry the tools home. {quest.ending}",
    ]
    world.say(ending_lines[params.ending % len(ending_lines)])

    world.facts.update(
        quest=quest,
        place=quest.place,
        threat=quest.threat,
        clue=quest.clue,
        false_lead=quest.false_lead,
        thought=quest.thought,
        tool=quest.tool,
        discovery=quest.discovery,
        cause=quest.cause,
        repair=quest.repair,
        proof=quest.proof,
        lesson=quest.lesson,
        ending=quest.ending,
        resolved=True,
    )
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    h, p, g = world.hero, world.partner, world.grizzly
    return [
        QAItem(
            question=f"What danger threatened {f['place']}?",
            answer=f"In {f['place']}, {f['threat']}.",
        ),
        QAItem(
            question=f"Which clue guided {h.id}'s search?",
            answer=f"{h.id} followed {f['clue']}, because that clue explained where the trouble had traveled.",
        ),
        QAItem(
            question=f"What did {g.id} admit?",
            answer=f"{g.id} admitted that the grizzly {f['cause']}.",
        ),
        QAItem(
            question="How did the heroes terminate the danger?",
            answer=f"They used {f['tool']} and {f['repair']}. Then they checked that {f['proof']}.",
        ),
        QAItem(
            question="Why was the ending happy?",
            answer=f"The team solved the danger without abandoning the grizzly, and {f['ending']}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet stream of thoughts a character hears inside their own mind.",
        ),
        QAItem(
            question="What does terminate mean?",
            answer="Terminate means to bring something to an end or make it stop.",
        ),
        QAItem(
            question="What is a grizzly?",
            answer="A grizzly is a large brown bear. In this story, the grizzly character is treated as a feeling helper who can learn and make repairs.",
        ),
        QAItem(
            question="What does scour mean?",
            answer="To scour means to search a place very carefully, often looking in many corners.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending shows that the main danger has been solved and that the characters are safe, wiser, or able to celebrate together.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly superhero story set in {f['place']} where a grizzly danger must be terminated safely.",
        f"Use an inner monologue as {world.hero.id} follows this clue: {f['clue']}. Include a quest, a helpful dialogue exchange, and a happy ending.",
        "Use the words terminate, grizzly, and scour naturally in a story about courage, evidence, and repair.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    entities = [world.hero, world.partner, world.grizzly, world.signal, world.place]
    for entity in entities:
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:10} ({entity.kind:9}) "
            f"meters={meters} memes={memes} location={entity.location or '-'}"
        )
    lines.append(f"  resolved={world.facts.get('resolved', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(superhero_quest).
requires(superhero_quest, terminate).
requires(superhero_quest, grizzly).
requires(superhero_quest, scour).
feature(superhero_quest, inner_monologue).
feature(superhero_quest, quest).
feature(superhero_quest, happy_ending).

valid_story(S) :-
    setting(S),
    requires(S, terminate),
    requires(S, grizzly),
    requires(S, scour),
    feature(S, inner_monologue),
    feature(S, quest),
    feature(S, happy_ending).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    facts = [
        asp.fact("setting", "superhero_quest"),
        asp.fact("requires", "superhero_quest", "terminate"),
        asp.fact("requires", "superhero_quest", "grizzly"),
        asp.fact("requires", "superhero_quest", "scour"),
        asp.fact("feature", "superhero_quest", "inner_monologue"),
        asp.fact("feature", "superhero_quest", "quest"),
        asp.fact("feature", "superhero_quest", "happy_ending"),
    ]
    return "\n".join(facts)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    models = asp.one_model(asp_program("#show valid_story/1."))
    valid = any(atom.name == "valid_story" for atom in models)
    if not valid:
        print("MISMATCH: ASP rules rejected the superhero quest.")
        return 1

    for i in range(len(QUESTS)):
        params = StoryParams(quest=i, seed=i)
        sample = generate(params)
        required = ("terminate", "grizzly", "scour")
        if not all(word in sample.story.lower() for word in required):
            print("MISMATCH: generated story omitted a required seed word.")
            return 1
        if not sample.world or not sample.world.facts.get("resolved"):
            print("MISMATCH: generated story did not resolve its world state.")
            return 1

    print("OK: ASP and Python recognize the complete superhero quest domain.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Superhero quests with inner monologue and happy endings."
    )
    parser.add_argument("--hero", default=None)
    parser.add_argument("--partner", default=None)
    parser.add_argument("--grizzly", default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random,
    sample_seed: int,
    base_seed: int,
) -> StoryParams:
    hero = args.hero or rng.choice(["Luna", "Nova", "Skye", "Comet", "Ruby"])
    partner = args.partner or rng.choice(["Max", "Pip", "Juno", "Kai", "Sol"])
    grizzly = args.grizzly or rng.choice(["Brumble", "Gizmo", "Tumble", "Moss"])
    if hero == partner:
        raise StoryError("The hero and partner must have different names.")
    if grizzly in {hero, partner}:
        raise StoryError("The grizzly must have a name different from the heroes.")
    offset = sample_seed - base_seed
    return StoryParams(
        hero=hero,
        partner=partner,
        grizzly=grizzly,
        quest=offset % len(QUESTS),
        voice=(offset // len(QUESTS)) % 4,
        ending=(offset // (len(QUESTS) * 4)) % 4,
        seed=sample_seed,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(hero="Luna", partner="Max", grizzly="Brumble", quest=0, seed=0),
    StoryParams(hero="Nova", partner="Pip", grizzly="Gizmo", quest=1, seed=1),
    StoryParams(hero="Skye", partner="Juno", grizzly="Tumble", quest=2, seed=2),
    StoryParams(hero="Comet", partner="Kai", grizzly="Moss", quest=3, seed=3),
    StoryParams(hero="Ruby", partner="Sol", grizzly="Brumble", quest=4, seed=4),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show valid_story/1."))
        print("ASP model:", [str(atom) for atom in model])
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 50)
        while len(samples) < args.n and index < limit:
            sample_seed = base_seed + index
            params = resolve_params(
                args,
                random.Random(sample_seed),
                sample_seed,
                base_seed,
            )
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
