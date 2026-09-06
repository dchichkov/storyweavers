#!/usr/bin/env python3
"""
Animal-story world: a blase animal, a canned treat, sharing, and inner monologue.

A small classical story simulation about a pet or woodland animal who acts
blase about a canned snack, thinks to itself, and learns to share.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StorySample  # noqa: E402


@dataclass
class Creature:
    name: str
    species: str
    role: str = "animal"
    kind: str = "character"
    meters: dict[str, float] = field(default_factory=lambda: {"hunger": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"blase": 0.0, "kindness": 0.0, "greed": 0.0, "joy": 0.0})
    inventory: list[str] = field(default_factory=list)

    def pronoun(self) -> str:
        return "it"

    def poss(self) -> str:
        return "its"


@dataclass
class CannedItem:
    label: str = "canned treat"
    kind: str = "food"
    sealed: bool = True
    opened: bool = False
    shared_with: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {"fullness": 1.0})
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Setting:
    place: str = "the sunny yard"
    description: str = "a quiet place with a bowl, a fence, and a warm patch of grass"


@dataclass
class StoryParams:
    place: str = "the sunny yard"
    hero_name: str = "Milo"
    hero_species: str = "cat"
    friend_name: str = "Pip"
    friend_species: str = "rabbit"
    scenario_id: int = 0
    telling_mode: int = 0
    thought_mode: int = 0
    ending_mode: int = 0
    seed: Optional[int] = None


@dataclass(frozen=True)
class Scenario:
    premise: str
    problem: str
    first_attempt: str
    clue: str
    discovery: str
    shared_jobs: str
    resolution: str
    lesson: str
    ending: str


SCENARIOS = (
    Scenario(
        premise="A windstorm had knocked seed packets across the yard, and the two animals had spent all morning gathering them.",
        problem="Only one sealed canned treat remained in the storm basket, while both workers' stomachs rumbled.",
        first_attempt="tried to hide the can beneath a broad leaf",
        clue="a seed packet skittered back toward the fence because one pair of paws could not hold the basket and catch it",
        discovery="the morning's work had succeeded only when they took turns helping",
        shared_jobs="held the basket steady while {friend} fetched the safe pull-tab opener",
        resolution="They divided the animal-safe treat into two clean bowls, then finished securing the seeds together.",
        lesson="help received should be answered with help freely given",
        ending="the last seed packet rested dry in the basket beside two empty bowls",
    ),
    Scenario(
        premise="A canned treat rolled from a delivery crate and stopped beside a narrow drain.",
        problem="The can began inching toward the drain whenever the floorboards trembled, and neither animal could save it alone.",
        first_attempt="pressed one paw against the can and pretended the wobble did not matter",
        clue="the can rolled only when the loose gate thumped in the wind",
        discovery="one animal needed to brace the can while the other latched the gate",
        shared_jobs="blocked the drain with a wooden scoop while {friend} fastened the gate latch",
        resolution="Once the can was safe, they asked the keeper to open it and shared equal spoonfuls.",
        lesson="sharing work can protect the thing everyone hopes to share",
        ending="the quiet gate cast a striped shadow across two polished bowls",
    ),
    Scenario(
        premise="A faded label on a canned treat showed two different feeding marks, one for small animals and one for large ones.",
        problem="The friends disagreed about the fair portions because each had read a different side of the wrinkled label.",
        first_attempt="turned the can so only the larger mark showed",
        clue="a loose corner of paper hid the words 'per animal'",
        discovery="fair sharing did not always mean identical scoops",
        shared_jobs="smoothed the label while {friend} brought the keeper's measuring cup",
        resolution="They measured the safe amount for each species and saved the remainder in a covered dish.",
        lesson="a fair share considers what each friend safely needs",
        ending="two different-sized servings sat side by side beneath the flattened label",
    ),
    Scenario(
        premise="The friends found a canned treat in the emergency cupboard just as rainwater crept under the porch door.",
        problem="They were hungry, but the can had to stay dry for the evening shelter meal.",
        first_attempt="nudged it toward a private corner before anyone else noticed",
        clue="three smaller animals arrived carrying dry towels for the same shelter",
        discovery="the emergency food belonged to the whole group, not to whoever saw it first",
        shared_jobs="stacked the towels into a barrier while {friend} carried the can to a high shelf",
        resolution="After the leak was stopped, the keeper opened the can and portioned it among everyone who had helped.",
        lesson="shared supplies remain useful when a community guards them together",
        ending="rain tapped the roof while a ring of clean bowls shone below the dry shelf",
    ),
    Scenario(
        premise="A canned treat was the prize at the end of a scent trail laid for the animals' enrichment game.",
        problem="The trail split at a stump, and {hero} wanted both the prize and all the credit.",
        first_attempt="raced down the strongest-smelling path without telling {friend}",
        clue="that path ended at an empty tin lid while faint paw marks continued the other way",
        discovery="{friend}'s careful eyes and {hero}'s keen nose solved different halves of the trail",
        shared_jobs="followed the scent while {friend} tracked the tiny prints",
        resolution="They reached the real can together, asked for it to be opened, and shared the reward.",
        lesson="a victory built from two talents belongs to both teammates",
        ending="the two trails met beside paired bowls and a stump covered in silver dew",
    ),
    Scenario(
        premise="During a picnic, a shiny canned treat reflected sunlight toward a nest of sleepy birds.",
        problem="The flashes startled the birds each time the can turned, yet {hero} was reluctant to move its special snack.",
        first_attempt="sat in front of the glare and acted as though the chirping were unimportant",
        clue="the bright patch crossed the nest whenever a cloud moved away",
        discovery="the can's curved metal, not the birds, was causing the commotion",
        shared_jobs="carried a shade cloth while {friend} guided the unopened can into a cool basket",
        resolution="Far from the nest, they had the treat opened safely and shared it without another flash.",
        lesson="noticing another creature's discomfort is part of being kind",
        ending="the nest grew still as two friends ate beneath the green shade cloth",
    ),
    Scenario(
        premise="A canned treat meant for the afternoon snack had a small dent along its rim.",
        problem="{hero} wanted to open it immediately, but the safety rule said damaged cans must be checked by a grown keeper.",
        first_attempt="tapped the dent and announced that waiting was needless",
        clue="{friend} found the red inspection tag tucked beneath the basket",
        discovery="being generous also meant refusing to share food that might be unsafe",
        shared_jobs="carried the tag to the keeper while {friend} marked the can's location",
        resolution="The keeper set the dented can aside and opened an undamaged canned treat for them to share.",
        lesson="safe sharing matters more than fast sharing",
        ending="a red tag fluttered on the closed can while two safe bowls cooled nearby",
    ),
    Scenario(
        premise="The animals were packing a wagon for a meadow cleanup when a canned treat would not fit under the tool box.",
        problem="Every new arrangement crushed either the snack basket or the soft work gloves.",
        first_attempt="kept the can in its own corner and let {friend}'s gloves hang over the edge",
        clue="an empty divider could stand upright instead of lying flat",
        discovery="making room for another's belongings did not reduce the value of one's own",
        shared_jobs="turned the divider while {friend} nested the small tools inside it",
        resolution="The gloves and can fit securely, and after the cleanup the friends shared the canned treat.",
        lesson="sharing space is often the first step toward sharing a reward",
        ending="the tidy wagon waited beside two bowls and a meadow free of litter",
    ),
    Scenario(
        premise="A cold morning left frost around the pantry latch where a canned treat was stored.",
        problem="The latch would not lift, and {hero} grew tempted to claim the treat if it managed the door alone.",
        first_attempt="scratched at the frozen latch until its paw became sore",
        clue="{friend}'s warm breath melted a tiny clear circle in the frost",
        discovery="gentle warmth worked better than force, especially when two friends took turns",
        shared_jobs="wrapped the latch in a warm cloth while {friend} fetched the keeper",
        resolution="The keeper opened the pantry and the can, then helped them share the snack in warm bowls.",
        lesson="patient cooperation can open what stubbornness cannot",
        ending="two curls of steam rose while the last patch of frost slipped from the latch",
    ),
    Scenario(
        premise="At a woodland fair, each team received one canned treat and a map to the communal supper table.",
        problem="A fallen branch covered the shortest path, and {hero} considered taking a secret shortcut alone.",
        first_attempt="squeezed beneath the branch with the can and left {friend} holding the map",
        clue="the shortcut circled back to the same mossy stone",
        discovery="the can was no use without the map, and the map was hard to carry without help",
        shared_jobs="carried the can in a sling while {friend} read the landmarks aloud",
        resolution="They reached the supper together and added their opened treat to the shared dishes.",
        lesson="staying together can be quicker than chasing a private shortcut",
        ending="their empty sling hung beside a supper table bright with many little bowls",
    ),
    Scenario(
        premise="A canned treat sat beside a donation basket labeled 'one for now, one for later.'",
        problem="{hero} had one can and could not decide whether later meant itself or a hungry neighbor.",
        first_attempt="slid the can toward its den while avoiding {friend}'s questioning look",
        clue="inside the basket lay a thank-you card from an animal helped the week before",
        discovery="someone else's earlier sharing had stocked the very can now in front of them",
        shared_jobs="read the card aloud while {friend} fetched two reusable bowls",
        resolution="They shared half, sealed the rest safely, and returned another can to the donation basket the next day.",
        lesson="generosity can travel in a circle through a neighborhood",
        ending="a fresh thank-you card leaned against the basket beside a newly donated can",
    ),
    Scenario(
        premise="{hero} had promised a canned treat for a moonlight story circle, but the friends arrived with more listeners than expected.",
        problem="There was not enough for full bowls, and canceling would disappoint everyone.",
        first_attempt="whispered that perhaps only the first two animals should eat",
        clue="{friend} noticed a basket of safe crunchy sides that each guest had brought",
        discovery="the canned treat could become one shared part of a larger meal",
        shared_jobs="portioned the treat into small toppings while {friend} arranged the contributed sides",
        resolution="Every listener received a safe supper, and each animal added one line to the story circle.",
        lesson="sharing ideas and small portions can make a gathering abundant",
        ending="twelve bowls formed a crescent beneath the moon as the final story line faded",
    ),
)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, eid: str, obj: object) -> object:
        self.entities[eid] = obj
        return obj

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _animal_article(species: str) -> str:
    return "an" if species[:1].lower() in "aeiou" else "a"


def _place_phrase(place: str) -> str:
    lowered = place.lower()
    if "porch" in lowered:
        return f"on {place}"
    if "yard" in lowered or "barn" in lowered:
        return f"in {place}"
    return f"at {place}"


def _render(text: str, hero: Creature, friend: Creature) -> str:
    return text.format(hero=hero.name, friend=friend.name)


def _opening(mode: int, world: World, hero: Creature, friend: Creature, scenario: Scenario) -> list[str]:
    location = _place_phrase(world.setting.place)
    introductions = (
        f"There {location}, {hero.name} the {hero.species} and {friend.name} the {friend.species} had already done a useful morning's work.",
        f"This animal story began {location}, where {hero.name}, {_animal_article(hero.species)} {hero.species}, shared the path with {friend.name}, {_animal_article(friend.species)} {friend.species}.",
        f"Morning found two neighbors {location}: {hero.name} the {hero.species}, quick to shrug, and {friend.name} the observant {friend.species}.",
        f"While they walked {location}, {friend.name} heard {hero.name} say, 'Nothing today could surprise me.' The {hero.species} tried to sound wonderfully unimpressed.",
        f"The day seemed ordinary to {hero.name}, {_animal_article(hero.species)} {hero.species} {location}. Beside it walked {friend.name}, {_animal_article(friend.species)} {friend.species} who noticed small details.",
        f"Before snack time {location}, {hero.name} and {friend.name} were neighbors but not yet practiced partners.",
        f"A quiet adventure waited {location}. It found {hero.name} the {hero.species} wearing an unimpressed expression and {friend.name} the {friend.species} ready to help.",
        f"'{hero.name} never makes a fuss,' {hero.name} liked to think. That belief was about to be tested beside {friend.name} {location}.",
    )
    return [introductions[mode % len(introductions)], _render(scenario.premise, hero, friend)]


def _thought(mode: int, hero: Creature, friend: Creature, scenario: Scenario) -> str:
    thoughts = (
        f"Inside, {hero.name} thought, 'If I share the can, will there be enough left for me?'",
        f"Its thoughts were less calm than its face: 'I want that canned treat, but {friend.name} has worked too.'",
        f"'I could pretend not to notice,' {hero.name} thought, 'yet pretending will not solve this.'",
        f"A private thought pricked {hero.name}: 'Keeping everything may be easy, but would it be fair?'",
        f"{hero.name} told itself, 'First learn what is happening. Then decide how the treat should be shared.'",
        f"Though its whiskers looked calm, {hero.name} wondered, 'What clue am I ignoring because I want the can?'",
        f"Quietly, {hero.name} admitted, 'I need {friend.name}'s help more than I need to look important.'",
        f"{hero.name} paused. 'A good choice should fix the problem and leave room for both of us,' it thought.",
    )
    return thoughts[mode % len(thoughts)]


def _ending(mode: int, hero: Creature, friend: Creature, scenario: Scenario) -> list[str]:
    reflections = (
        f"{hero.name} learned that {scenario.lesson}.",
        f"'Next time, I will notice before I shrug,' {hero.name} told {friend.name}. Together they remembered that {scenario.lesson}.",
        f"The lesson stayed with both animals: {scenario.lesson}.",
        f"{friend.name} did not praise the size of the share; it praised the care behind it. {hero.name} understood that {scenario.lesson}.",
        f"What changed was not merely an empty can. {hero.name} now knew that {scenario.lesson}.",
        f"{hero.name}'s earlier pose had hidden uncertainty. Honest cooperation taught it that {scenario.lesson}.",
        f"They promised to use the same careful teamwork again, because {scenario.lesson}.",
        f"Sharing had become an action instead of a nice-sounding word, and {hero.name} saw that {scenario.lesson}.",
    )
    images = (
        f"At dusk, {scenario.ending}.",
        f"The final thing {hero.name} saw was this: {scenario.ending}.",
        f"When the light softened, {scenario.ending}.",
        f"Behind them, {scenario.ending}; ahead, the friends walked home together.",
        f"Their adventure ended quietly. There, {scenario.ending}.",
        f"{friend.name} smiled toward the place where {scenario.ending}.",
        f"No boast marked the ending, only this small picture: {scenario.ending}.",
        f"Long after the snack was gone, they remembered how {scenario.ending}.",
    )
    return [reflections[mode % len(reflections)], images[(mode * 3 + 1) % len(images)]]


def tell(params: StoryParams) -> World:
    world = World(Setting(place=params.place))
    hero = world.add("hero", Creature(name=params.hero_name, species=params.hero_species))
    friend = world.add("friend", Creature(name=params.friend_name, species=params.friend_species))
    can = world.add("can", CannedItem(label="canned animal-safe treat"))
    scenario = SCENARIOS[params.scenario_id % len(SCENARIOS)]

    hero.memes["blase"] = 1.0
    hero.meters["hunger"] = 0.5

    for sentence in _opening(params.telling_mode, world, hero, friend, scenario):
        world.say(sentence)
    world.say(
        "The word 'blase' means seeming unimpressed. It described the pose "
        f"{hero.name} was trying, not what kind of animal {hero.name} was."
    )

    world.para()
    world.say(_render(scenario.problem, hero, friend))
    world.say(f"At first, {hero.name} {_render(scenario.first_attempt, hero, friend)}.")
    world.say(f"{hero.name}'s inner monologue turned toward the choice it had to make.")
    world.say(_thought(params.thought_mode, hero, friend, scenario))
    world.say(f"'{hero.name}, look again,' said {friend.name}. 'The answer may be in what changed.'")

    world.para()
    world.say(f"The clue was clear: {_render(scenario.clue, hero, friend)}.")
    world.say(f"Then {hero.name} understood that {_render(scenario.discovery, hero, friend)}.")
    world.say(f"Instead of guarding the canned treat, {hero.name} {_render(scenario.shared_jobs, hero, friend)}.")
    world.say("Sharing the work made a fair and safe answer possible.")
    world.say(_render(scenario.resolution, hero, friend))

    can.sealed = False
    can.opened = True
    can.shared_with.append(friend.name)
    hero.meters["hunger"] += 0.5
    friend.meters["hunger"] += 0.5
    hero.memes["kindness"] += 1.0
    hero.memes["joy"] += 1.0
    friend.memes["joy"] += 1.0
    hero.memes["blase"] = 0.0
    world.events.extend(["problem_noticed", "clue_found", "jobs_shared", "treat_shared"])

    world.para()
    for sentence in _ending(params.ending_mode, hero, friend, scenario):
        world.say(_render(sentence, hero, friend))

    world.facts.update(
        hero=hero,
        friend=friend,
        can=can,
        params=params,
        setting=world.setting,
        scenario=scenario,
        problem=_render(scenario.problem, hero, friend),
        clue=_render(scenario.clue, hero, friend),
        discovery=_render(scenario.discovery, hero, friend),
        shared_jobs=_render(scenario.shared_jobs, hero, friend),
        resolution=_render(scenario.resolution, hero, friend),
        lesson=_render(scenario.lesson, hero, friend),
        ending=_render(scenario.ending, hero, friend),
        opened=True,
        shared=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Creature = f["hero"]
    friend: Creature = f["friend"]
    return [
        f"Write an animal story about {hero.name}, a {hero.species} acting blase, who faces this problem: {f['problem']}",
        f"Tell how {hero.name}'s inner monologue changes after this clue: {f['clue']}",
        f"Write a gentle story {_place_phrase(world.setting.place)} where {hero.name} and {friend.name} solve a problem and share a canned treat.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Creature = f["hero"]
    friend: Creature = f["friend"]
    return [
        QAItem(
            question=f"What problem did {hero.name} and {friend.name} face {_place_phrase(world.setting.place)}?",
            answer=f"They faced this problem: {f['problem']}"
        ),
        QAItem(
            question=f"What clue changed {hero.name}'s thinking?",
            answer=f"{hero.name} noticed that {f['clue']}. That clue helped the friends understand that {f['discovery']}."
        ),
        QAItem(
            question=f"How did the two animals work together before sharing the canned treat?",
            answer=f"{hero.name} {f['shared_jobs']}. Their teamwork made the safe resolution possible."
        ),
        QAItem(
            question=f"What lesson did {hero.name} learn from sharing with {friend.name}?",
            answer=f"{hero.name} learned that {f['lesson']}. By the end, {f['ending']}."
        ),
        QAItem(
            question=f"Was the canned treat opened and shared with {friend.name}?",
            answer=f"Yes. The treat was opened safely, and {friend.name} received a share after the animals solved the problem together."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use, enjoy, or eat part of something with you."
        ),
        QAItem(
            question="What is a canned food item?",
            answer="A canned food item is food sealed inside a metal can so it stays fresh until it is opened."
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet thinking a character does inside its own head."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


ASP_RULES = r"""
blase(H) :- hero(H).
opened(C) :- can(C), opened_can(C).
shared(H,F,C) :- opened(C), hero(H), friend(F), can(C).
happy(H) :- shared(H,_,_).
happy(F) :- shared(_,F,_).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero", "hero"),
        asp.fact("friend", "friend"),
        asp.fact("can", "can"),
        asp.fact("opened_can", "can"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with sharing and inner monologue.")
    ap.add_argument("--place", default=None)
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
    place = args.place or rng.choice(["the sunny yard", "the quiet porch", "the little barn"])
    return StoryParams(
        place=place,
        hero_name=rng.choice(["Milo", "Nori", "Penny", "Toto", "Luna"]),
        hero_species=rng.choice(["cat", "fox", "raccoon", "bear", "mouse"]),
        friend_name=rng.choice(["Pip", "Mimi", "Dot", "Bram", "Kiki"]),
        friend_species=rng.choice(["rabbit", "dog", "hedgehog", "squirrel", "duck"]),
        scenario_id=rng.randrange(len(SCENARIOS)),
        telling_mode=rng.randrange(8),
        thought_mode=rng.randrange(8),
        ending_mode=rng.randrange(8),
        seed=args.seed,
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


def dump_trace(world: World) -> str:
    hero: Creature = world.entities["hero"]
    friend: Creature = world.entities["friend"]
    can: CannedItem = world.entities["can"]
    return "\n".join([
        "--- world trace ---",
        f"place: {world.setting.place}",
        f"hero: {hero.name} {hero.species} meters={hero.meters} memes={hero.memes}",
        f"friend: {friend.name} {friend.species} meters={friend.meters} memes={friend.memes}",
        f"can: sealed={can.sealed} opened={can.opened} shared_with={can.shared_with}",
    ])


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:  # pragma: no cover
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show shared/3. #show happy/1."))
    shared = set(asp.atoms(model, "shared"))
    if ("hero", "friend", "can") not in shared:
        print("MISMATCH: ASP model did not derive sharing.")
        return 1
    print("OK: ASP twin derives sharing as expected.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show shared/3. #show happy/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show shared/3. #show happy/1."))
        print("shared:", asp.atoms(model, "shared"))
        print("happy:", asp.atoms(model, "happy"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        params_list = [
            StoryParams(place="the sunny yard", hero_name="Milo", hero_species="cat", friend_name="Pip", friend_species="rabbit"),
            StoryParams(place="the quiet porch", hero_name="Nori", hero_species="fox", friend_name="Mimi", friend_species="duck"),
            StoryParams(place="the little barn", hero_name="Penny", hero_species="bear", friend_name="Dot", friend_species="squirrel"),
        ]
        samples = [generate(p) for p in params_list]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

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


if __name__ == "__main__":
    main()
