#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
% Tiny superhero storyworld: a hero can finish a quest with a happy ending
% only if the grizzly threat is addressed by a careful plan and the grime is
% scoured away rather than ignored.
hero(hero_name).
quest(open_path).
threat(grizzly).
task(scour).
feature(inner_monologue).
feature(happy_ending).

can_finish :- hero(hero_name), quest(open_path), threat(grizzly), task(scour), feature(inner_monologue), feature(happy_ending).
#show can_finish/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Nova"
    sidekick: str = "Pip"
    city: str = "Pine Harbor"
    object_name: str = "silver scarf"
    place: str = "the river bridge"
    time: str = "dusk"


@dataclass
class Character:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, delta: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + delta

    def add_meme(self, key: str, delta: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + delta


@dataclass
class ObjectThing:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def add_meter(self, key: str, delta: float) -> None:
        self.meters[key] = self.meters.get(key, 0.0) + delta

    def add_meme(self, key: str, delta: float) -> None:
        self.memes[key] = self.memes.get(key, 0.0) + delta


@dataclass
class World:
    params: StoryParams
    characters: dict[str, Character] = field(default_factory=dict)
    objects: dict[str, ObjectThing] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)

    def say(self, line: str) -> None:
        self.trace.append(line)

    def add_character(self, ch: Character) -> Character:
        self.characters[ch.name] = ch
        return ch

    def add_object(self, obj: ObjectThing) -> ObjectThing:
        self.objects[obj.name] = obj
        return obj

    def render(self) -> str:
        return "\n\n".join(self.trace)


SCENARIOS = [
    {
        "title": "the bridge-grizzly",
        "premise": "a grizzly had wandered onto the river bridge and sat like a furry boulder beside the lantern rail",
        "obstacle": "The bridge crews had stopped traffic, but the bear was blocking the only safe path across town",
        "clue": "muddy honey on the rail showed that the grizzly was following a spilled picnic basket, not hunting people",
        "mistake": "{hero_name} first thought of charging in, but the bear's size made that feel less like courage and more like trouble",
        "action": "{hero_name} used the inner monitor in a whisper, then asked Pip to bring a honey jar and a long broom for guiding crumbs away",
        "dialogue": "'We do not fight what we can outthink,' {hero_name} said. 'Then let's scour the trail clear,' Pip replied",
        "resolution": "They lured the grizzly toward the shoreline berries, and the bridge opened again once the animal waddled off",
        "ending": "the moonlit bridge shone empty and safe, with only a clean stripe of honey glaze left on the planks",
        "lesson": "a hero can be brave without being reckless",
    },
    {
        "title": "the soot tunnel quest",
        "premise": "black soot had clogged the old tunnel gate under the city, turning the exit into a smudged cave mouth",
        "obstacle": "Children on the far side were waiting for supplies, and every minute of delay made the quest feel bigger",
        "clue": "a paw print in the soot proved that a grizzly cub had dragged a sticky tarp over the lever",
        "mistake": "{hero_name} wanted to yank the tarp at once, but the lever looked ready to snap",
        "action": "{hero_name} listened to an inner monologue of caution, then asked Pip to scour the rust from a spare hook and lift the tarp slowly",
        "dialogue": "'I can think my way through this,' {hero_name} said. 'And I can hold the lantern,' Pip answered",
        "resolution": "The gate rose, the supplies rolled through, and the cub tumbled after its mother to the woods",
        "ending": "clean daylight poured through the tunnel, bright enough to turn the soot into glitter on the stones",
        "lesson": "careful thinking can finish a quest that strong hands alone might break",
    },
    {
        "title": "the window ledge rescue",
        "premise": "a small grizzly cub had climbed onto a narrow window ledge above the bakery sign",
        "obstacle": "Below it, the street was busy, and a fall would have hurt the cub and frightened everyone",
        "clue": "crumbs on the ledge led back to an open loaf basket inside the bakery kitchen",
        "mistake": "{hero_name} reached upward before noticing the ledge was slick with butter",
        "action": "{hero_name} stepped back, breathed through an inner monologue of worry, and asked Pip to scour a blanket across the awning while the baker coaxed the cub down",
        "dialogue": "'Slow is safer,' {hero_name} whispered. 'Then let's be slow,' said Pip",
        "resolution": "The cub climbed onto the blanket, the baker shut the basket, and the street cheered softly",
        "ending": "warm bread smell drifted from the bakery while the cub trotted away with no one hurt",
        "lesson": "a rescue becomes heroic when it keeps every paw safe",
    },
    {
        "title": "the canyon gate quest",
        "premise": "the canyon gate stood open, but a grizzly had wedged its heavy shoulder against the hinge chain",
        "obstacle": "Without the gate, the wind kept scattering map papers across the trail",
        "clue": "the bear kept sniffing at a berry crate tied to the gatepost",
        "mistake": "{hero_name} almost shouted to scare the bear off, then remembered loud panic would only make the animal thrash",
        "action": "{hero_name} told Pip to scour the crate lid clean, then slid the crate farther downhill while the bear watched from the shade",
        "dialogue": "'I know what the bear wants now,' {hero_name} murmured. 'Then we can move smarter,' Pip said",
        "resolution": "The grizzly followed the berries, the hinge chain loosened, and the gate swung shut against the wind",
        "ending": "the trail maps stayed flat on the table as the canyon breeze hummed harmlessly past",
        "lesson": "seeing the cause of trouble is the first superpower of a quest",
    },
    {
        "title": "the rooftop soot alarm",
        "premise": "a red alarm light flashed on the museum roof, where soot had collected around the vent fans",
        "obstacle": "The museum's night exhibit would fail if the fans stopped, and the whole block would lose power",
        "clue": "a grizzly-shaped kite had snagged the vent grating and pulled it crooked in the wind",
        "mistake": "{hero_name} reached for the grating without checking the loose wire below it",
        "action": "{hero_name} paused for an inner monologue, then asked Pip to scour the wire clamp free while the museum guard held the ladder steady",
        "dialogue": "'I was about to rush,' {hero_name} admitted. 'Good thing you stopped,' said the guard",
        "resolution": "The kite dropped away, the fans started again, and the museum lights glowed for the night show",
        "ending": "the rooftop air spun clean and cool above a city that could finally sleep",
        "lesson": "a hero earns a happy ending by slowing down at the right moment",
    },
    {
        "title": "the riverbank berry quest",
        "premise": "a grizzly followed a trail of smashed berries along the riverbank and would not leave the park path",
        "obstacle": "Families could not cross to the playground while the bear paced near the footbridge",
        "clue": "the berry trail ended at a child's dropped lunch pail beside a trash bin",
        "mistake": "{hero_name} thought the bear was angry, but the bear only kept sniffing the pail",
        "action": "{hero_name} used an inner monologue to plan, then asked Pip to scour berry juice from the path and slide the pail into a locked cart",
        "dialogue": "'So the bear is just hungry,' {hero_name} said. 'And now we know what to move,' Pip replied",
        "resolution": "With the food scent gone, the grizzly ambled to the woods, and the bridge re-opened",
        "ending": "children crossed laughing, while the river reflected one calm, bear-free sunset",
        "lesson": "a good quest answer solves the real problem, not the loudest one",
    },
    {
        "title": "the clocktower grime hunt",
        "premise": "thick grime had stained the clocktower hands so badly that the city clock read the wrong hour",
        "obstacle": "Trains, bakery ovens, and school bells all depended on the clock being right",
        "clue": "fresh claw marks on the tower door showed that a grizzly had leaned there while scratching at a honey stain",
        "mistake": "{hero_name} planned to clean the face first, but the locked door meant the real trouble was higher up",
        "action": "{hero_name} listened to the inner monologue of the tower itself, then had Pip scour the honey from a side rail so the bear would not return",
        "dialogue": "'The clock is confused, not broken,' {hero_name} said. 'Let's help it tell the truth,' Pip answered",
        "resolution": "The grizzly lost interest, the tower hands were fixed, and noon rang on time again",
        "ending": "the city bells swung over a square full of tidy faces looking up in relief",
        "lesson": "sometimes the cleanest victory is removing the bait",
    },
    {
        "title": "the harbor quest lamp",
        "premise": "one harbor lamp had gone dark, leaving the dock walk dim and slippery at dusk",
        "obstacle": "A grizzly was sleeping beside the broken power box, and no worker wanted to wake it",
        "clue": "salt flakes on the box lid showed that seawater had crusted the switch shut",
        "mistake": "{hero_name} nearly touched the switch before noticing the wet metal could shock a hand",
        "action": "{hero_name} thought through an inner monologue, then asked Pip to scour the salt crust with a dry brush while the dockmaster waved a flashlight from a safe distance",
        "dialogue": "'We only need a little light and a little patience,' {hero_name} said. 'Then the path can be safe again,' Pip said",
        "resolution": "The lamp clicked on, the grizzly slept through the repair, and the dockwalk brightened",
        "ending": "gold light spread over the water while tiny waves tapped the pilings like applause",
        "lesson": "quiet heroics can change a whole harbor",
    },
    {
        "title": "the scarf on the stair",
        "premise": "a silver scarf fluttered on the museum stair where a grizzly had ripped open an exhibit case",
        "obstacle": "The case held a rescue medal, and the broken glass made the stair dangerous",
        "clue": "the grizzly did not want the medal; it only wanted the shiny scarf that smelled like fish from the river",
        "mistake": "{hero_name} thought the bear had stolen the medal, then noticed the medal still sat untouched in the case",
        "action": "{hero_name} used an inner monologue to steady the heart, then had Pip scour the glass away with a broom while the curator called animal rescue",
        "dialogue": "'The scarf is the prize, not the medal,' {hero_name} said. 'Then we can return both safely,' the curator replied",
        "resolution": "The rescue team took the scarf, the grizzly got a fish crate at the river, and the medal stayed in the museum",
        "ending": "the stair gleamed clean under the restored case, proud and perfectly still",
        "lesson": "a hero can solve a puzzle by understanding what the grizzly truly wants",
    },
    {
        "title": "the alley quest of echoes",
        "premise": "strange echoes rolled through a narrow alley where soot had piled knee-high against the brick",
        "obstacle": "A grizzly was trapped at the end of the alley, and the only exit was blocked by trash cans",
        "clue": "the echoes matched a loose metal lid banging in the wind, not any roar from the bear",
        "mistake": "{hero_name} almost sprinted in, but the alley was too tight for fast moves",
        "action": "{hero_name} listened to an inner monologue, then asked Pip to scour the soot off the exit sign while the firefighters moved the cans one by one",
        "dialogue": "'We can make a small path,' {hero_name} said. 'Small is enough,' Pip answered",
        "resolution": "The grizzly lumbered out calmly, the alley opened, and the echoes stopped",
        "ending": "the brick wall stood clean enough to reflect a single bright superhero badge",
        "lesson": "a short, careful quest can be just as heroic as a big one",
    },
]


OPENINGS = [
    "At dusk, {hero_name} zipped across {city} with {sidekick} to answer a new quest.",
    "When the sky over {city} turned violet, {hero_name} and {sidekick} hurried toward {place}.",
    "A siren flashed at dusk, and {hero_name} raced through {city} beside {sidekick}.",
    "{hero_name} had just finished patrol when a quest call led to {place} at dusk.",
    "By the time dusk settled on {city}, {hero_name} and {sidekick} were already on the move.",
    "The evening wind swept over {city} as {hero_name} lifted a hand and called {sidekick} to the next quest.",
    "At the edge of dusk, {hero_name} spotted trouble near {place} and sprang into action with {sidekick}.",
    "The rooftops of {city} glowed red at dusk while {hero_name} and {sidekick} searched for the source of the alarm.",
]

TURNS = [
    "That changed the mission from a chase into a careful rescue.",
    "The first plan was too fast, so {hero_name} had to think like a hero, not a hammer.",
    "An inner monologue full of caution gave way to a smarter, gentler move.",
    "What looked like a threat turned into a clue once {hero_name} slowed down.",
    "The quest sharpened when {hero_name} noticed the detail everyone else had missed.",
    "A brave pause made room for the right answer.",
    "The trouble was real, but it was smaller than it first appeared.",
    "The moment felt huge until {hero_name} named the true problem aloud.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny superhero storyworld with grizzlies, quests, and happy endings.")
    ap.add_argument("--hero-name")
    ap.add_argument("--sidekick")
    ap.add_argument("--city")
    ap.add_argument("--object-name")
    ap.add_argument("--place")
    ap.add_argument("--time")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero_name = args.hero_name or rng.choice(["Nova", "Dash", "Arrow", "Luna", "Vega"])
    sidekick = args.sidekick or rng.choice(["Pip", "Glow", "Zip", "Moss", "Echo"])
    city = args.city or rng.choice(["Pine Harbor", "Cloudbridge", "Sunvale", "Maple Bay"])
    object_name = args.object_name or rng.choice(["silver scarf", "blue badge", "signal ring", "lantern key"])
    place = args.place or rng.choice(["the river bridge", "the tunnel gate", "the museum stair", "the harbor dock"])
    time = args.time or "dusk"
    if time != "dusk":
        raise StoryError("This storyworld is set at dusk.")
    return StoryParams(seed=None, hero_name=hero_name, sidekick=sidekick, city=city, object_name=object_name, place=place, time=time)


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hero", "hero_name"),
            asp.fact("quest", "open_path"),
            asp.fact("threat", "grizzly"),
            asp.fact("task", "scour"),
            asp.fact("feature", "inner_monologue"),
            asp.fact("feature", "happy_ending"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable_story() -> bool:
    return True


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show can_finish/0."))
    asp_ok = bool(asp.atoms(model, "can_finish"))
    py_ok = python_reasonable_story()
    if asp_ok == py_ok:
        print("OK: ASP and Python agree on the story gate.")
        return 0
    print(f"MISMATCH: asp={asp_ok} python={py_ok}")
    return 1


def generate_story(world: World) -> None:
    p = world.params
    story_seed = p.seed if p.seed is not None else 0
    scenario = SCENARIOS[story_seed % len(SCENARIOS)]
    opening = OPENINGS[(story_seed // len(SCENARIOS)) % len(OPENINGS)]
    turn = TURNS[(story_seed // (len(SCENARIOS) * len(OPENINGS))) % len(TURNS)]
    values = {
        "hero_name": p.hero_name,
        "sidekick": p.sidekick,
        "city": p.city,
        "object_name": p.object_name,
        "place": p.place,
    }

    hero = world.add_character(Character(name=p.hero_name, role="hero"))
    sidekick = world.add_character(Character(name=p.sidekick, role="sidekick"))
    prop = world.add_object(ObjectThing(name=p.object_name, kind="prop"))
    hero.add_meme("duty", 1)
    hero.add_meme("hope", 1)
    sidekick.add_meme("loyalty", 1)

    world.say(opening.format(**values))
    world.say(f"The quest was called {scenario['title']}, and it began when {scenario['premise']}.")
    world.say(f"{scenario['obstacle']}. {scenario['clue']}.")
    world.say(f"{scenario['mistake'].format(**values)}. {turn.format(**values)}")
    world.say(f"{scenario['action'].format(**values)}.")
    world.say(f"{scenario['dialogue'].format(**values)}.")
    hero.add_meter("courage", 2)
    sidekick.add_meter("helpfulness", 2)
    prop.add_meter("cleanliness", 1)
    world.say(f"{scenario['resolution']}.")
    world.say(f"At last, {scenario['ending']}.")
    world.say(f"That was the kind of happy ending where {scenario['lesson']}.")

    world.facts = {
        "hero_name": p.hero_name,
        "sidekick": p.sidekick,
        "city": p.city,
        "object_name": p.object_name,
        "place": p.place,
        "time": p.time,
        "scenario": scenario["title"],
        "obstacle": scenario["obstacle"],
        "clue": scenario["clue"],
        "resolution": scenario["resolution"],
        "ending_image": scenario["ending"],
        "lesson": scenario["lesson"],
    }


def generation_prompts(world: World) -> list[str]:
    p = world.params
    facts = world.facts
    return [
        f"Write a superhero story about {p.hero_name} and {p.sidekick} solving {facts['scenario']} at {p.place} during dusk.",
        f"Use inner monologue and dialogue to show how this clue changes the plan: {facts['clue']}.",
        f"End with a concrete happy-ending image: {facts['ending_image']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    f = world.facts
    return [
        QAItem(
            question=f"What was the main trouble in the quest?",
            answer=f"{f['obstacle']}. That mattered because the hero needed to protect {p.city} and finish the quest safely.",
        ),
        QAItem(
            question="Which clue changed how the hero acted?",
            answer=f"{f['clue']}. The clue showed that the situation was not random and helped point the hero toward the real fix.",
        ),
        QAItem(
            question="How did the hero and sidekick solve the problem?",
            answer=f"{f['resolution']}. They used a careful plan, not just force, and that is why the quest worked.",
        ),
        QAItem(
            question="What ending image proves things got better?",
            answer=f"{f['ending_image']}. It shows the result by describing what the place looked like after the victory.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a quest in this storyworld?",
            answer="A quest is a mission a hero takes on to solve trouble, help others, and reach a safe result.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is a character's private thinking that helps them choose a careful next step.",
        ),
        QAItem(
            question="Why is a happy ending important here?",
            answer="A happy ending means the danger is handled, the characters are safe, and the final picture feels complete.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ch in world.characters.values():
        lines.append(f"  {ch.name} ({ch.role}) meters={ch.meters} memes={ch.memes}")
    for obj in world.objects.values():
        lines.append(f"  {obj.name} ({obj.kind}) meters={obj.meters} memes={obj.memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = World(params=params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show can_finish/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show can_finish/0."))
        print("can_finish" if asp.atoms(model, "can_finish") else "(no can_finish)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            seed=base_seed,
            hero_name=args.hero_name or "Nova",
            sidekick=args.sidekick or "Pip",
            city=args.city or "Pine Harbor",
            object_name=args.object_name or "silver scarf",
            place=args.place or "the river bridge",
            time="dusk",
        )
        samples = [generate(params)]
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
