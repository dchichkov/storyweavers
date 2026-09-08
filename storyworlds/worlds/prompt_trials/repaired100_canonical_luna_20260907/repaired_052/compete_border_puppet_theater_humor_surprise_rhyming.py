#!/usr/bin/env python3
"""
A small standalone puppet-theater storyworld about two performers who compete
across a painted border, discover a surprise, and use humor to share the stage.
"""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "actress"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "actor"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Theater:
    name: str
    setting: str = "the puppet theater"
    border: str = "a red-and-gold curtain border"
    stage: str = "the little wooden stage"
    surprise: str = "a springy puppet door"


@dataclass
class World:
    theater: Theater
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    puppeteer: str
    rival: str
    theater_name: str
    show_title: str
    place: str
    seed: Optional[int] = None
    scenario: Optional[str] = None
    telling_mode: Optional[str] = None


@dataclass(frozen=True)
class Scenario:
    key: str
    premise: str
    border_detail: str
    contest: str
    mishap: str
    clue: str
    reveal: str
    shared_action: str
    outcome: str
    lesson: str
    ending: str


PUPPETEERS = ["Luna", "Milo", "Pia", "Nico", "Tara", "Bibi"]
RIVALS = ["Pip", "Dot", "Rolo", "Tilly", "Bram", "Kiki"]
THEATERS = [
    "the Moonbeam Puppet Theater",
    "the Buttonwood Puppet Theater",
    "the Lantern Puppet Theater",
    "the Bluebird Puppet Theater",
]
PLACES = [
    "the village square",
    "the old market lane",
    "the riverside fair",
    "the school garden",
]
SHOW_TITLES = [
    "The Dragon Who Lost His Sock",
    "The Cow Who Wore a Crown",
    "The Great Turnip Parade",
    "The Mouse and the Moon",
]
TELLING_MODES = ["arrival", "warning", "dialogue", "countdown", "mystery", "promise"]

SCENARIOS = [
    Scenario(
        key="dragon_sock",
        premise="was preparing a puppet contest about a tiny dragon searching for a missing sock",
        border_detail="the painted border showed blue clouds on one side and yellow moons on the other",
        contest="to make the funniest dragon entrance",
        mishap="the dragon puppet bounced over the border and landed in the rival's scene",
        clue="the puppet's loose sock was tied to a hidden spring beneath the stage",
        reveal="the border was not a wall at all but a shared trapdoor for comic entrances",
        shared_action="turned the spring into a seesaw and made both puppets tumble into the same scene",
        outcome="the audience laughed so warmly that neither performer wanted to win alone",
        lesson="a contest can become better when laughter makes room for two players",
        ending="the dragon wore one sock on each foot while the painted border twinkled behind him",
    ),
    Scenario(
        key="crowned_cow",
        premise="was staging a royal puppet race between a proud cow and a very slow snail",
        border_detail="the curtain border was stitched with tiny crowns and bright green vines",
        contest="to see whose puppet could cross the stage first",
        mishap="the cow's paper crown snagged on the border and pulled the whole curtain sideways",
        clue="the crown's ribbon tugged whenever the snail's shell rolled near the curtain",
        reveal="the border hid a second track that made slow puppets look wonderfully grand",
        shared_action="opened both tracks and let the cow race while the snail received a royal parade",
        outcome="the audience cheered for the fast winner and the slow winner in equal measure",
        lesson="humor grows when different kinds of winning are welcomed",
        ending="the cow bowed at the finish while the snail rolled past in a crown twice its size",
    ),
    Scenario(
        key="turnip_parade",
        premise="was rehearsing a puppet parade led by a boastful turnip with a feather hat",
        border_detail="the border was painted with striped flags that seemed to wave on their own",
        contest="to give the grandest parade speech",
        mishap="the turnip's grand bow knocked a button loose and sent the border marching across the stage",
        clue="the moving flags kept stopping beside a small red foot pedal",
        reveal="the border was a playful puppet drum controlled by that pedal",
        shared_action="played the border like a drum while both performers made the turnip dance",
        outcome="the speech became a silly parade song and every child joined the beat",
        lesson="a mistake can become a joke when people investigate it together",
        ending="the turnip bowed to a marching curtain, and the curtain bowed right back",
    ),
    Scenario(
        key="moon_mouse",
        premise="was presenting two puppet explorers who claimed to be first at the moon",
        border_detail="the painted border glittered with stars and a crooked silver line",
        contest="to prove which explorer deserved the brightest spotlight",
        mishap="both puppets pulled the same moon rope and dropped the border between them",
        clue="a soft squeak came from inside the fallen strip of cloth",
        reveal="a shy moon mouse had been living in the border and was tugging the stars",
        shared_action="gave the mouse a tiny lantern and made it the guide for both explorers",
        outcome="the explorers stopped arguing and followed the mouse through a moonlit dance",
        lesson="surprise can turn a quarrel into teamwork when everyone gets a part",
        ending="the moon mouse led the bow, and even the stars seemed to clap",
    ),
    Scenario(
        key="backward_bear",
        premise="was readying a bear puppet who told every joke backward",
        border_detail="the border carried two painted arrows pointing in opposite directions",
        contest="to see which performer could make the audience laugh first",
        mishap="the bear crossed the border backward and tangled both puppeteers' strings",
        clue="each tangled string made the bear's backward jokes come out almost right",
        reveal="the border marked a secret turning place where jokes changed direction",
        shared_action="took turns crossing the mark and built one joke from two funny halves",
        outcome="the audience laughed at the shared punch line instead of choosing a champion",
        lesson="cooperation can make a joke land when competition only makes it stumble",
        ending="the bear bowed backward, then forward, and the whole theater roared",
    ),
    Scenario(
        key="rainy_rabbit",
        premise="was performing a rabbit weather show with two puppets claiming the best forecast",
        border_detail="the curtain border was dotted with little cloth raindrops",
        contest="to predict whether the puppet sky would rain or shine",
        mishap="a hidden water pouch popped and sent raindrops over both sides of the stage",
        clue="the drops fell only when both puppeteers pulled their weather strings",
        reveal="the border joined the two weather puppets into one silly storm machine",
        shared_action="pulled together and made a rainbow shower for the rabbit audience",
        outcome="the rival forecasts became one bright weather dance",
        lesson="when two guesses meet, curiosity may reveal a better answer",
        ending="the rabbit shared one umbrella with the sun puppet beneath a cloth rainbow",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Puppet theater storyworld about competition, borders, humor, and surprise."
    )
    parser.add_argument("--puppeteer", choices=PUPPETEERS)
    parser.add_argument("--rival", choices=RIVALS)
    parser.add_argument("--theater-name")
    parser.add_argument("--show-title")
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--scenario", choices=[s.key for s in SCENARIOS])
    parser.add_argument("--telling-mode", choices=TELLING_MODES)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    puppeteer = args.puppeteer or rng.choice(PUPPETEERS)
    rival_choices = [name for name in RIVALS if name != puppeteer]
    rival = args.rival or rng.choice(rival_choices)
    return StoryParams(
        puppeteer=puppeteer,
        rival=rival,
        theater_name=args.theater_name or rng.choice(THEATERS),
        show_title=args.show_title or rng.choice(SHOW_TITLES),
        place=args.place or rng.choice(PLACES),
        scenario=args.scenario or rng.choice(SCENARIOS).key,
        telling_mode=args.telling_mode or rng.choice(TELLING_MODES),
    )


def asp_facts() -> str:
    import asp

    facts = [
        asp.fact("domain", "puppet_theater"),
        asp.fact("feature", "humor"),
        asp.fact("feature", "surprise"),
        asp.fact("theme", "compete"),
        asp.fact("object", "border"),
        asp.fact("style", "rhyming_story"),
        asp.fact("rule", "share_the_stage"),
    ]
    return "\n".join(facts)


ASP_RULES = r"""
#show domain/1.
#show feature/1.
#show theme/1.
#show object/1.
#show style/1.
#show rule/1.
safe_story :- domain(puppet_theater), feature(humor), feature(surprise),
              theme(compete), object(border), style(rhyming_story),
              rule(share_the_stage).
#show safe_story/0.
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show safe_story/0."))
    if ("safe_story",) in [(symbol.name,) for symbol in model if symbol.name == "safe_story"]:
        print("OK: ASP twin contains the puppet-theater story requirements.")
        return 0
    print("MISMATCH: ASP twin did not derive safe_story.")
    return 1


def _opening(params: StoryParams, scenario: Scenario) -> list[str]:
    mode = params.telling_mode or "arrival"
    name = params.puppeteer
    rival = params.rival
    theater = params.theater_name
    place = params.place

    if mode == "warning":
        return [
            f'"Mind the border!" cried {rival} as {theater} opened in {place}.',
            f"{name} was ready with puppets and plans; {scenario.premise}.",
        ]
    if mode == "dialogue":
        return [
            f'"I will win the laugh contest," said {name}. "We shall see," said {rival}.',
            f"At {theater}, in {place}, {scenario.premise}.",
        ]
    if mode == "countdown":
        return [
            f"Three, two, one—the curtain rose at {theater} in {place}.",
            f"Before the first drum could ring, {name} and {rival} {scenario.premise}.",
        ]
    if mode == "mystery":
        return [
            f"A tiny giggle came from the border of {theater}.",
            f"{name} and {rival} leaned close while {scenario.premise}.",
        ]
    if mode == "promise":
        return [
            f"{name} had promised a marvelous show at {theater}, so the puppeteer hurried to {place}.",
            f"But {scenario.premise}.",
        ]
    return [
        f"At {theater} in {place}, {name} and {rival} raised their puppets beneath the lights.",
        f"They {scenario.premise}.",
    ]


def generate(params: StoryParams) -> StorySample:
    if not params.puppeteer or not params.rival:
        raise StoryError("A puppet show needs both a puppeteer and a rival.")
    if params.puppeteer == params.rival:
        raise StoryError("The puppeteer and rival must be different characters.")
    scenario = next((s for s in SCENARIOS if s.key == params.scenario), None)
    if scenario is None:
        raise StoryError(f"Unknown puppet-theater scenario: {params.scenario}")

    rng = random.Random(params.seed)
    theater = Theater(name=params.theater_name, setting=params.place)
    world = World(theater)

    lead = world.add(
        Entity(
            id=params.puppeteer,
            kind="character",
            type="puppeteer",
            label="first puppeteer",
            phrase=params.puppeteer,
            location="left side of stage",
            meters={"confidence": 0.8, "tension": 0.5},
            memes={"humor": 0.7, "competition": 0.8},
            traits=["inventive", "eager"],
        )
    )
    rival = world.add(
        Entity(
            id=params.rival,
            kind="character",
            type="puppeteer",
            label="second puppeteer",
            phrase=params.rival,
            location="right side of stage",
            meters={"confidence": 0.7, "tension": 0.5},
            memes={"humor": 0.6, "competition": 0.8},
            traits=["quick", "proud"],
        )
    )
    border = world.add(
        Entity(
            id="stage_border",
            kind="thing",
            type="border",
            label="painted stage border",
            phrase="the painted stage border",
            location="between the scenes",
            meters={"rigidity": 0.8, "mystery": 0.9},
            memes={"separation": 0.8, "surprise": 0.8},
            traits=["striped", "wobbly"],
        )
    )
    puppet = world.add(
        Entity(
            id="featured_puppet",
            kind="thing",
            type="puppet",
            label="featured puppet",
            phrase="the featured puppet",
            owner=params.puppeteer,
            location="stage",
            meters={"comic_energy": 0.8},
            memes={"curiosity": 0.7},
        )
    )

    world.facts.update(
        params=params,
        scenario=scenario.key,
        setting="puppet theater",
        feature_humor=True,
        feature_surprise=True,
        seed_words=["compete", "border"],
        opening=scenario.premise,
        obstacle=scenario.mishap,
        clue=scenario.clue,
        reveal=scenario.reveal,
        repair=scenario.shared_action,
        outcome=scenario.outcome,
    )

    for sentence in _opening(params, scenario):
        world.say(sentence)
    world.say(f'"First across the {theater.border}, first to the cheer!" {lead.phrase} announced.')
    world.say(f'"Then let us compete fair and square," {rival.phrase} replied, with a bow that was nearly a tumble.')

    world.para()
    world.say(f"The contest began {scenario.contest}.")
    world.say(f"At once, {scenario.mishap}.")
    world.say(f"The puppets wobbled, the curtains wiggled, and the audience giggled.")
    world.say(f'"That border is blocking my best joke!" cried {lead.phrase}.')
    world.say(f'"Or hiding your best surprise," answered {rival.phrase}. "Let us look before we tug."')

    world.para()
    world.say(f"They watched carefully and noticed that {scenario.clue}.")
    world.say(f"That small clue led to a big surprise: {scenario.reveal}.")
    world.say(f"{lead.phrase} lowered the puppet, and {rival.phrase} lowered the curtain.")
    world.say(f'"What if we make the border part of the show?" asked {lead.phrase}.')
    world.say(f'"A shared joke beats a lonely victory," said {rival.phrase}.')

    world.para()
    world.say(f"Together they {scenario.shared_action}.")
    world.say(f"The new scene was so silly that one puppet bowed to the wrong side, while the other sneezed a cloth star.")
    world.say(f"Then {scenario.outcome}.")
    world.say(f"The performers stopped trying to outshine one another and let the laughter belong to everyone.")

    world.para()
    world.say(f"They learned that {scenario.lesson}.")
    world.say(f"The border still marked the stage, but it no longer kept the friends apart.")
    world.say(f"As the final bell rang, {scenario.ending}.")

    border.location = "shared comic doorway"
    border.meters["rigidity"] = 0.2
    border.meters["mystery"] = 0.1
    border.memes["separation"] = 0.1
    border.memes["shared_play"] = 1.0
    lead.meters["tension"] = 0.0
    rival.meters["tension"] = 0.0
    lead.memes["cooperation"] = 1.0
    rival.memes["cooperation"] = 1.0
    puppet.location = "shared stage"
    world.facts.update(resolved=True, shared_stage=True, humor_used=True, surprise_revealed=True)

    prompts = [
        f"Write a rhyming-style puppet-theater story where {params.puppeteer} and {params.rival} compete across a border, then discover a funny surprise.",
        f"Tell a humorous story in {params.theater_name} about this surprise: {scenario.reveal}.",
        f"Write a child-friendly puppet show ending that proves {scenario.lesson}.",
    ]
    story_qa = [
        QAItem(
            question=f"Who competed in the puppet theater?",
            answer=f"{params.puppeteer} and {params.rival} competed in the puppet theater at {params.theater_name}.",
        ),
        QAItem(
            question="What happened at the border?",
            answer=f"{scenario.mishap}. The trouble interrupted their contest and made the puppets wobble.",
        ),
        QAItem(
            question="What surprise did the performers discover?",
            answer=f"They discovered that {scenario.reveal}.",
        ),
        QAItem(
            question="How did the performers solve the problem?",
            answer=f"They worked together and {scenario.shared_action}. This turned the contest into a shared comic scene.",
        ),
        QAItem(
            question="What changed by the end of the show?",
            answer=f"The border became part of their shared performance, and they learned that {scenario.lesson}.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a puppet theater?",
            answer="A puppet theater is a place where performers move puppets behind or above a stage to tell a story.",
        ),
        QAItem(
            question="What does it mean to compete?",
            answer="To compete means to try to do well while another person is trying too, often by following fair rules.",
        ),
        QAItem(
            question="Why can humor help a story?",
            answer="Humor can make a tense moment gentler and help characters notice a friendly way to solve a problem.",
        ),
        QAItem(
            question="What is a border?",
            answer="A border is an edge or dividing line that marks where one space or picture ends and another begins.",
        ),
    ]
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- world model state ---")
        for entity in sample.world.entities.values():
            details = []
            if entity.location:
                details.append(f"location={entity.location}")
            if entity.meters:
                details.append(f"meters={entity.meters}")
            if entity.memes:
                details.append(f"memes={entity.memes}")
            print(f"  {entity.id}: {entity.type} {' '.join(details)}")
    if qa:
        print()
        print("== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show safe_story/0."))
        return

    if args.verify:
        status = asp_verify()
        if status:
            sys.exit(status)
        verify_params = StoryParams(
            puppeteer="Luna",
            rival="Pip",
            theater_name="the Moonbeam Puppet Theater",
            show_title="The Dragon Who Lost His Sock",
            place="the village square",
            seed=17,
            scenario="dragon_sock",
            telling_mode="dialogue",
        )
        sample = generate(verify_params)
        required = ["border", "surprise", "compete"]
        if not all(word in sample.story.lower() for word in required):
            print("MISMATCH: generated story lacks a required story word.")
            sys.exit(1)
        if len(sample.story_qa) < 3 or not sample.world.facts.get("shared_stage"):
            print("MISMATCH: generated story did not resolve its world state.")
            sys.exit(1)
        print("OK: Python generation exercised with required story features.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                puppeteer="Luna",
                rival="Pip",
                theater_name="the Moonbeam Puppet Theater",
                show_title="The Dragon Who Lost His Sock",
                place="the village square",
                seed=101,
                scenario="dragon_sock",
                telling_mode="dialogue",
            ),
            StoryParams(
                puppeteer="Milo",
                rival="Dot",
                theater_name="the Buttonwood Puppet Theater",
                show_title="The Cow Who Wore a Crown",
                place="the old market lane",
                seed=202,
                scenario="crowned_cow",
                telling_mode="warning",
            ),
            StoryParams(
                puppeteer="Pia",
                rival="Rolo",
                theater_name="the Lantern Puppet Theater",
                show_title="The Mouse and the Moon",
                place="the riverside fair",
                seed=303,
                scenario="moon_mouse",
                telling_mode="mystery",
            ),
        ]
        samples = [generate(params) for params in curated]
    else:
        if args.n < 1:
            raise StoryError("-n must be at least 1.")
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 20):
            attempt += 1
            attempt_seed = base_seed + attempt
            params = resolve_params(args, random.Random(attempt_seed))
            params.seed = attempt_seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show safe_story/0."))
        print("ASP model:", ", ".join(str(symbol) for symbol in model))
        return

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if args.all:
            params = sample.params
            header = f"### {params.puppeteer} and {params.rival} at {params.theater_name}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
