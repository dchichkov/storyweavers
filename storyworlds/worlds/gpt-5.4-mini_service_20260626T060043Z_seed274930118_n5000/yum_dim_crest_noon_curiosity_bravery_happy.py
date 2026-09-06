#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
% Registry facts define the small world.
place(crest).
time(noon).
feature(curiosity).
feature(bravery).
feature(happy_ending).

% A safe, bedtime-story resolution exists when curiosity meets a gentle test
% and bravery helps reach the crest before noon ends.
can_reach(crest) :- place(crest).
gentle_test(curiosity) :- feature(curiosity).
helpful(bravery) :- feature(bravery).
ending(happy) :- feature(happy_ending).

happy_story :- can_reach(crest), gentle_test(curiosity), helpful(bravery), ending(happy).
#show happy_story/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Mina"
    companion: str = "a sleepy lantern"
    snack: str = "warm honey toast"
    object_name: str = "the small silver key"
    place: str = "the crest"
    time: str = "noon"


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
        "title": "the dim signal window",
        "premise": "a dim green blink winked from the old lookout window",
        "obstacle": "Mist had hidden the trail markers, and a young courier below could not see the safe turn",
        "clue": "three bright scratches beside the window matched the three trail posts",
        "mistake": "At first, {name} nearly hurried uphill without telling anyone",
        "action": "{name} called to Ranger Ivo, then polished the dusty signal glass while Ivo reset the markers",
        "dialogue": "'Being brave can mean asking for help,' {name} said",
        "resolution": "Together they flashed three clear signals, and the courier found the safe path",
        "ending": "three green squares shone across the valley like tiny windows in the sun",
        "lesson": "curiosity gathers clues, while bravery uses them responsibly",
    },
    {
        "title": "the noon-bell nest",
        "premise": "the noon bell made only a dim little hum instead of its round bong",
        "obstacle": "Without the bell, the hill gardeners would not know when to open the shade cloths",
        "clue": "a strand of blue grass poked from the bell's wooden wheel",
        "mistake": "{name} wanted to tug the wheel at once, but stopped when a frightened chirp came from inside",
        "action": "{name} fetched Keeper Ada, held the ladder steady, and watched as she moved a wren's nest to a sheltered basket",
        "dialogue": "'A mystery is not permission to grab,' {name} whispered",
        "resolution": "The wheel turned freely, the bell rang, and the wrens stayed snug beside it",
        "ending": "the last bong floated above the crest while four beaks opened for lunch",
        "lesson": "bravery can be patient and gentle with smaller lives",
    },
    {
        "title": "the missing picnic shadow",
        "premise": "a picnic table cast a dim, crooked shadow although the noon sun stood overhead",
        "obstacle": "The bent shade frame was slowly pulling loose above a family picnic",
        "clue": "one brass pin lay under a patch of crushed clover",
        "mistake": "{name} first blamed the wind, then noticed the wind chimes were perfectly still",
        "action": "{name} moved everyone clear, showed the pin to Park Worker Sol, and helped sort the repair bolts by size",
        "dialogue": "'The shadow told us where to look,' {name} explained",
        "resolution": "Sol secured the frame before anyone sat beneath it again",
        "ending": "a straight square of shade held a red lunch cloth covered in safe, happy crumbs",
        "lesson": "curiosity becomes useful when observations lead to careful action",
    },
    {
        "title": "the thirsty crest garden",
        "premise": "the crest garden looked dim and droopy at noon while one stone channel sparkled",
        "obstacle": "Water was skipping the seedlings and spilling toward the path",
        "clue": "a line of wet pawprints ended beside a gate made from twigs",
        "mistake": "{name} almost swept the twigs away before noticing they formed a beaver's careful dam",
        "action": "{name} asked Gardener Mei to guide the water through a second shallow channel that left the little dam alone",
        "dialogue": "'We can help the flowers without wrecking another builder's work,' {name} said",
        "resolution": "Both channels filled: one for the garden and one for the beaver's pool",
        "ending": "water beads trembled on twelve bright leaves as a brown nose surfaced nearby",
        "lesson": "a brave solution protects more than one neighbor",
    },
    {
        "title": "the kite beyond the rail",
        "premise": "a yellow kite fluttered dimly below the crest's noon lookout",
        "obstacle": "Its string was looped around a branch beyond the safety rail",
        "clue": "each gust lifted the kite close enough for a long hook, but never for a reaching hand",
        "mistake": "{name} put one foot toward the rail and immediately stepped back",
        "action": "{name} told Coach Ren, tied a ribbon to mark the danger, and helped join two approved kite poles",
        "dialogue": "'I want the kite, but I want everyone safe more,' {name} said",
        "resolution": "Ren freed the string from firm ground, and its owner thanked the whole team",
        "ending": "the yellow kite climbed above the crest with a new blue tail snapping happily",
        "lesson": "bravery is choosing the safe plan even when the risky one looks faster",
    },
    {
        "title": "the echo under the stones",
        "premise": "a dim tap-tap answered every noon footstep near the crest marker",
        "obstacle": "One paving stone had loosened above a hollow rain channel",
        "clue": "the sound grew sharper beside a hair-thin crack and softer two steps away",
        "mistake": "{name} wondered whether treasure was underneath, but did not pry at the stone",
        "action": "{name} drew a chalk circle around the crack and brought Mason Jo to inspect it",
        "dialogue": "'The echo is exciting, but a loose stone needs an expert,' {name} said",
        "resolution": "Jo reset the stone and showed how the channel safely carried storm water downhill",
        "ending": "clean water chimed below the firm path while chalk stars ringed the finished repair",
        "lesson": "curiosity asks what is hidden, and bravery keeps the question safe",
    },
    {
        "title": "the dim map room",
        "premise": "the tiny map room at the crest stayed dim even at bright noon",
        "obstacle": "Visitors were bumping the display ropes because the mirror lantern had turned away from its window",
        "clue": "a narrow stripe of sunlight ended on a shiny screw beneath the map case",
        "mistake": "{name} tried waving {object_name} in the light, but its flash was too brief to guide anyone",
        "action": "{name} closed the room, fetched Guide Laleh, and described exactly where the light stripe stopped",
        "dialogue": "'My idea failed, but the clue did not,' {name} said",
        "resolution": "Laleh tightened the mirror lantern and reopened the room after checking every walkway",
        "ending": "a warm ribbon of noon light crossed the map from the river to the painted crest",
        "lesson": "a failed guess can still lead a curious mind toward the truth",
    },
    {
        "title": "the marmot's noon alarm",
        "premise": "a marmot gave one dim squeak from beneath the crest steps at noon",
        "obstacle": "A fallen food tin had wedged beside its burrow entrance",
        "clue": "fresh soil curved around the tin, and tiny claw marks pointed outward",
        "mistake": "{name} wanted to pull the tin free, but the steep stones wobbled underfoot",
        "action": "{name} backed away, kept visitors quiet, and guided Wildlife Carer Bo to the exact spot",
        "dialogue": "'Courage does not need to be loud,' {name} told {companion}",
        "resolution": "Bo removed the tin with a reacher and checked that the burrow remained sound",
        "ending": "the marmot popped into the noon light, whiskers dusty and eyes wonderfully bright",
        "lesson": "noticing trouble and calling the right helper is a brave deed",
    },
    {
        "title": "the upside-down crest flag",
        "premise": "the crest flag hung dim and upside down at noon",
        "obstacle": "Hikers below mistook its old distress pattern for a warning and began turning back",
        "clue": "two ropes crossed at the pulley, but only the blue rope trembled when the flag moved",
        "mistake": "{name} guessed which rope to pull, then remembered that guessing could knot them tighter",
        "action": "{name} described the crossing to Warden Priya and helped hold the rope labels where she could see them",
        "dialogue": "'Let's be certain before we act,' {name} said",
        "resolution": "Priya untangled the pulley, raised the flag correctly, and radioed the hikers that the path was open",
        "ending": "the bright crest flag opened flat against a clean blue patch of sky",
        "lesson": "careful certainty is stronger than a hurried show of courage",
    },
    {
        "title": "the humming lunch box",
        "premise": "a forgotten lunch box gave a dim hum beside the crest sundial at noon",
        "obstacle": "Everyone worried that something trapped inside might be hurt",
        "clue": "the hum stopped whenever a cloud covered the little solar fan on its lid",
        "mistake": "{name} nearly opened the unknown box, then chose not to touch it",
        "action": "{name} kept the path clear and asked Ranger Ivo to check the owner's label and latch",
        "dialogue": "'I am curious enough to wonder and brave enough to wait,' {name} said",
        "resolution": "Ivo found a harmless cooling fan and returned the box to a relieved young hiker",
        "ending": "the fan purred beside a shared lunch, and everyone cried, 'Yum!' over crisp apple slices",
        "lesson": "good questions do not require unsafe answers",
    },
    {
        "title": "the clouded noon compass",
        "premise": "the crest compass looked dim under a sudden noon cloud and pointed toward the cliff path",
        "obstacle": "A walking group began following the false needle away from the marked trail",
        "clue": "the needle swung whenever a visitor's metal water bottle passed near it",
        "mistake": "{name} felt shy about interrupting the grown-ups, but tested the clue twice from a safe spot",
        "action": "{name} spoke clearly to Guide Laleh, who moved the bottles and checked the compass against her map",
        "dialogue": "'The needle changes near the bottles,' {name} explained",
        "resolution": "The group returned to the marked trail before the cloud thickened",
        "ending": "silver trail dots glimmered homeward as the compass settled north",
        "lesson": "bravery can be speaking up when evidence says something is wrong",
    },
    {
        "title": "the lantern seed surprise",
        "premise": "a row of dim paper lanterns appeared around the crest exactly at noon",
        "obstacle": "Their strings crossed the accessible path, and nobody knew who had placed them",
        "clue": "each lantern held seed paper and one letter of a message from the hill gardeners",
        "mistake": "{name} first thought the mysterious row should stay untouched",
        "action": "{name} found Gardener Mei, then helped move the lanterns onto low hooks beside the path",
        "dialogue": "'A surprise can change without being spoiled,' {name} said",
        "resolution": "The cleared path welcomed every visitor, and the letters spelled PLANT KINDNESS",
        "ending": "at sunset, children tucked the seed-paper letters into soil beneath twelve glowing lanterns",
        "lesson": "curiosity and bravery can make a happy surprise kinder for everyone",
    },
]


OPENINGS = [
    "At bright noon, {name} reached {place} with {companion} and a parcel of {snack}.",
    "The noon sun sat over {place} when {name} arrived, sharing {snack} with {companion}.",
    "Just as the clock marked noon, {name} and {companion} climbed to {place} for {snack}.",
    "{name} had planned a quiet noon picnic of {snack} at {place}, with {companion} close by.",
    "Noon painted the path to {place} gold as {name} carried {snack} beside {companion}.",
    "With {companion} keeping pace, {name} brought {snack} to {place} at noon.",
    "At noon, the promise of {snack} drew {name} and {companion} toward {place}.",
    "{name} reached {place} at noon, hungry for {snack} and curious about the hilltop.",
    "The bells had just announced noon when {name}, {companion}, and {snack} arrived at {place}.",
    "A warm noon breeze followed {name} and {companion} up to {place}, where {snack} waited.",
]


TURNS = [
    "That small clue changed the whole adventure.",
    "Instead of charging ahead, {name} let the evidence choose the next step.",
    "Curiosity supplied a question; bravery supplied a careful choice.",
    "The mystery became less frightening once {name} named what was known.",
    "A brave breath did not erase the worry, but it made room for a sensible plan.",
    "Then {name} noticed the detail that everyone else had missed.",
    "The first idea was not the best one, and {name} was brave enough to change it.",
    "Listening closely turned a puzzling moment into a problem they could solve.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime-story world: curiosity, bravery, and a happy ending at the crest."
    )
    ap.add_argument("--name")
    ap.add_argument("--companion")
    ap.add_argument("--snack")
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
    name = args.name or rng.choice(["Mina", "Eli", "Sora", "Nia", "Tomas"])
    companion = args.companion or rng.choice(["a sleepy lantern", "a soft moon kitten", "a tiny blanket"])
    snack = args.snack or rng.choice(["warm honey toast", "apple slices", "oat porridge"])
    object_name = args.object_name or rng.choice(["the small silver key", "the nest-shaped locket", "the round tin star"])
    place = args.place or "the crest"
    time = args.time or "noon"
    if place != "the crest":
        raise StoryError("This world is built around the crest.")
    if time != "noon":
        raise StoryError("This world is built around noon.")
    return StoryParams(
        seed=None,
        name=name,
        companion=companion,
        snack=snack,
        object_name=object_name,
        place=place,
        time=time,
    )


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("place", "crest"),
            asp.fact("time", "noon"),
            asp.fact("feature", "curiosity"),
            asp.fact("feature", "bravery"),
            asp.fact("feature", "happy_ending"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_story/0."))
    asp_ok = bool(asp.atoms(model, "happy_story"))
    py_ok = python_reasonable_story()
    if asp_ok == py_ok:
        print("OK: ASP and Python agree on the happy story gate.")
        return 0
    print(f"MISMATCH: asp={asp_ok} python={py_ok}")
    return 1


def python_reasonable_story() -> bool:
    return True


def generate_story(world: World) -> None:
    p = world.params
    story_seed = p.seed if p.seed is not None else 0
    scenario = SCENARIOS[story_seed % len(SCENARIOS)]
    opening = OPENINGS[(story_seed // len(SCENARIOS)) % len(OPENINGS)]
    turn = TURNS[(story_seed // (len(SCENARIOS) * len(OPENINGS))) % len(TURNS)]
    values = {
        "name": p.name,
        "companion": p.companion,
        "snack": p.snack,
        "object_name": p.object_name,
        "place": p.place,
    }

    def line(key: str) -> str:
        return scenario[key].format(**values)

    def sentence(key: str) -> str:
        text = line(key)
        return text[0].upper() + text[1:]

    child = world.add_character(Character(name=p.name, role="child"))
    companion = world.add_object(ObjectThing(name=p.companion, kind="companion"))
    clue_object = world.add_object(ObjectThing(name=p.object_name, kind="keepsake"))

    child.add_meme("curiosity", 1)
    child.add_meme("bravery", 0.25)
    child.add_meme("hope", 0.5)

    world.say(opening.format(**values))
    world.say(
        f"Tucked beside {p.object_name} was a card labeled YUM: enjoy {p.snack}, use curiosity, "
        f"and leave {p.place} happier than you found it. {p.name} liked that sort of invitation."
    )
    world.say(f"The first mystery was {scenario['title']}: {line('premise')}.")
    world.say(f"{sentence('obstacle')}. {sentence('clue')}.")

    child.add_meter("steps", 8)
    companion.add_meter("encouragement", 1)
    world.say(f"{line('mistake')}. {turn.format(**values)}")
    world.say(f"{line('action')}. {line('dialogue')}.")

    child.add_meme("bravery", 1)
    child.add_meme("care", 1)
    clue_object.add_meter("usefulness", 1)
    world.say(f"{line('resolution')}. The worry loosened, and everyone finally shared {p.snack}. 'Yum,' they agreed.")

    child.add_meme("joy", 1)
    world.say(
        f"{p.name} understood that {line('lesson')}. That was bravery with thought behind it, "
        "not bravery for show."
    )
    world.say(
        f"It was a happy ending at {p.place}: {line('ending')}. "
        f"As noon softened into afternoon, {p.name} carried {p.object_name} home beside {p.companion}."
    )

    world.facts = {
        "name": p.name,
        "companion": p.companion,
        "snack": p.snack,
        "object_name": p.object_name,
        "place": p.place,
        "time": p.time,
        "scenario": scenario["title"],
        "obstacle": sentence("obstacle"),
        "clue": sentence("clue"),
        "action": sentence("action"),
        "resolution": sentence("resolution"),
        "lesson": line("lesson"),
        "ending_image": line("ending"),
    }


def story_qa(world: World) -> list[QAItem]:
    p = world.params
    facts = world.facts
    return [
        QAItem(
            question=f"What problem did {p.name} discover during {facts['scenario']}?",
            answer=f"{facts['obstacle']}. The problem mattered because someone or something at {p.place} needed a safe response.",
        ),
        QAItem(
            question=f"Which clue helped {p.name} decide what to do?",
            answer=f"{facts['clue']}. {p.name} paid attention to that evidence instead of rushing toward the first guess.",
        ),
        QAItem(
            question=f"How did {p.name} act with curiosity and bravery?",
            answer=f"{facts['action']}. This was brave because {p.name} chose a careful, useful action even when the situation felt uncertain.",
        ),
        QAItem(
            question="How was the problem resolved?",
            answer=f"{facts['resolution']}. The solution followed the clue and left the crest safer than before.",
        ),
        QAItem(
            question="What concrete image closes the happy ending?",
            answer=f"The final image is this: {facts['ending_image']}. It shows the result rather than merely saying that everyone was happy.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn what is hidden or new.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is when someone does something hard or scary even while their heart is beating fast.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the trouble is solved and the story closes with safety, comfort, and joy.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.params
    facts = world.facts
    return [
        f"Write a child-facing story about {p.name} solving {facts['scenario']} at the crest at noon.",
        f"Tell how curiosity reveals this clue: {facts['clue']}. Show bravery through a safe, thoughtful action.",
        f"End happily with this concrete image: {facts['ending_image']}.",
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
        print(asp_program("#show happy_story/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show happy_story/0."))
        print("happy_story" if asp.atoms(model, "happy_story") else "(no happy_story)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            seed=base_seed,
            name=args.name or "Mina",
            companion=args.companion or "a sleepy lantern",
            snack=args.snack or "warm honey toast",
            object_name=args.object_name or "the small silver key",
            place="the crest",
            time="noon",
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
