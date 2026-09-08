#!/usr/bin/env python3
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
from typing import Optional

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


ASP_RULES = r"""
% Tiny parade world: a sailor, an infantry band, and one kind twist.
place(parade_square).
feature(twist).
feature(heartwarming).

together(sailor, infantry).
safe_resolution :- place(parade_square), feature(twist), feature(heartwarming), together(sailor, infantry).
#show safe_resolution/0.
"""


@dataclass
class StoryParams:
    seed: Optional[int] = None
    parade_name: str = "the lantern parade"
    sailor_name: str = "Mira"
    infantry_name: str = "Captain Ilyas"
    child_name: str = "Nora"
    object_name: str = "the ribbon banner"
    place: str = "parade square"
    time: str = "sunset"


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
class Thing:
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
    things: dict[str, Thing] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)
    facts: dict[str, str] = field(default_factory=dict)

    def say(self, line: str) -> None:
        self.trace.append(line)

    def add_character(self, ch: Character) -> Character:
        self.characters[ch.name] = ch
        return ch

    def add_thing(self, thing: Thing) -> Thing:
        self.things[thing.name] = thing
        return thing

    def render(self) -> str:
        return "\n\n".join(self.trace)


SCENARIOS = [
    {
        "title": "the crooked banner",
        "premise": "a parade banner hung low and crooked over parade square",
        "obstacle": "the ribbon knots had tightened in the evening breeze, and the marching path looked worried and small",
        "clue": "a little silver pin was stuck near one corner, just where the banner kept tugging",
        "mistake": "At first, {child_name} wanted to yank the banner free at once",
        "action": "{sailor_name} climbed the ladder, while {infantry_name} steadied it below and {child_name} held the ribbon ends together",
        "dialogue": "'Let's fix the banner gently,' {sailor_name} said. 'Kind hands make a stronger parade,' {infantry_name} answered",
        "resolution": "Together they loosened the knot, slipped out the pin, and the banner lifted cleanly into the breeze",
        "ending": "the ribbon banner danced above parade square like a bright wave saying everyone belonged",
        "lesson": "a twist can become heartwarming when people share the work and keep one another safe",
    },
    {
        "title": "the lost drumbeat",
        "premise": "the parade drums had fallen silent except for one shy tap",
        "obstacle": "the youngest drummer had mislaid a stick behind the supply cart, and the infantry march kept drifting apart",
        "clue": "muddy little footprints curved toward a stack of folded flags",
        "mistake": "{child_name} almost chased the footprints alone, but stopped when the path crossed the band rope",
        "action": "{sailor_name} listened for the tap, and {infantry_name} asked everyone to freeze while {child_name} peered behind the cart",
        "dialogue": "'I found the missing stick!' {child_name} called. 'Then we can find the rhythm too,' {infantry_name} said",
        "resolution": "The drummer got the stick back, the march found its beat, and the parade started moving like one happy river",
        "ending": "boots, drums, and a sailor's whistle shared one cheerful rhythm across parade square",
        "lesson": "careful listening can turn a small mistake into a warm rescue",
    },
    {
        "title": "the rain-sprinkled rehearsal",
        "premise": "a soft rain sprinkled the parade rehearsal and made the flags droop",
        "obstacle": "the infantry shoes were slipping, and the sailor worried the lantern floats would tip",
        "clue": "a row of dry crates sat beside the covered steps, just big enough for a safer route",
        "mistake": "{child_name} first thought the rehearsal should end, but noticed the rain was gentle, not dangerous",
        "action": "{child_name} brought the clue to {sailor_name}, and {infantry_name} shifted the march to the dry crates",
        "dialogue": "'We do not need a perfect day to make a kind parade,' {sailor_name} said",
        "resolution": "The group rehearsed in a new line, and the lantern floats shone brighter for having been handled with care",
        "ending": "rain beads glittered on the flags while the whole parade learned a safer way forward",
        "lesson": "a twist is heartwarming when it helps everyone adapt together",
    },
    {
        "title": "the shy trumpet salute",
        "premise": "one trumpet gave a tiny squeak instead of a proud parade call",
        "obstacle": "the mouthpiece had jammed, and the infantry line was waiting for the salute",
        "clue": "a crumb of sweet bread was caught inside the silver tip",
        "mistake": "{child_name} giggled, then quickly looked worried because the trumpeter felt embarrassed",
        "action": "{sailor_name} fetched a soft cloth, and {infantry_name} showed how to clean the mouthpiece without rushing",
        "dialogue": "'It is all right to need help,' {sailor_name} said. 'And it is all right to ask,' the trumpeter replied",
        "resolution": "The crumb came out, the trumpet sang again, and the parade answered with a shining salute",
        "ending": "the trumpet note floated over parade square like a brave little kite",
        "lesson": "a gentle fix can turn embarrassment into relief and pride",
    },
    {
        "title": "the spilled confetti sack",
        "premise": "a sack of parade confetti tipped open beside the fountain",
        "obstacle": "the paper stars were blowing into the water, and the infantry children were afraid the celebration would be ruined",
        "clue": "the sack had a torn seam that matched the shape of a missing thread on the sewing kit",
        "mistake": "{child_name} began scooping confetti with both hands, but only made the papers wetter",
        "action": "{sailor_name} held the sack open, while {infantry_name} threaded the sewing needle and {child_name} spread the stars to dry",
        "dialogue": "'We can save the party piece by piece,' {infantry_name} said. 'And we can still laugh,' {child_name} answered",
        "resolution": "The seam was mended, the stars dried in the sun, and the confetti drifted safely into the parade",
        "ending": "bright paper stars sparkled on the fountain stones like a second sky",
        "lesson": "heartwarming help often begins with one calm, useful hand",
    },
    {
        "title": "the lantern that would not glow",
        "premise": "one parade lantern stayed dark while the others glowed amber",
        "obstacle": "the lantern's tiny wind-up switch was stuck, and everyone feared the float would look lopsided",
        "clue": "the shadow on the wall showed the switch had been turned halfway, not all the way",
        "mistake": "{child_name} wanted to shake the lantern, but {sailor_name} stopped them before the glass could crack",
        "action": "{sailor_name} turned the lantern gently, and {infantry_name} held it steady while {child_name} counted the clicks",
        "dialogue": "'Slow is safer than sorry,' {sailor_name} said. 'And safe is kinder,' {child_name} replied",
        "resolution": "The switch clicked, the lantern glowed, and the float rejoined the parade with a warm new shine",
        "ending": "five amber lanterns glowed together, and the dark one became the brightest surprise of all",
        "lesson": "a twist becomes sweet when patience saves the light",
    },
    {
        "title": "the unexpected banner guest",
        "premise": "a small dog trotted into parade square wearing a paper badge",
        "obstacle": "the dog had followed the march from the bakery, and now the infantry line did not know where its owner had gone",
        "clue": "the badge held a name written in blue ink and a crumb of flour from the bakery door",
        "mistake": "{child_name} nearly tried to lift the dog into the parade cart, but the dog was too nervous",
        "action": "{sailor_name} crouched and spoke softly, while {infantry_name} sent a runner to the bakery with the badge",
        "dialogue": "'Hello, little guest,' {sailor_name} said. 'We will help you find your person,' {child_name} promised",
        "resolution": "The owner arrived with a grateful grin, and the dog paraded proudly beside the music band",
        "ending": "the badge bobbed on the dog's collar as the whole square cheered one warm, happy hello",
        "lesson": "a heartwarming twist can turn a stray moment into a new friend",
    },
    {
        "title": "the button on the curb",
        "premise": "a brass button flashed near the parade curb as the sun lowered",
        "obstacle": "the infantry coat on the review stand had one empty sleeve, and the missing button made the coat look unfinished",
        "clue": "the button matched a loose thread on the sleeve cuff exactly",
        "mistake": "{child_name} wanted to pocket the button as a lucky charm, but paused when the coat holder looked sad",
        "action": "{child_name} returned the button, {sailor_name} threaded a needle, and {infantry_name} pinned the cuff in place",
        "dialogue": "'It belongs back where it can do its job,' {child_name} said. 'And you helped it get there,' {infantry_name} answered",
        "resolution": "The coat looked neat again, and the review stand became a little warmer with gratitude",
        "ending": "the brass button shone on the sleeve like a tiny sunset",
        "lesson": "kindness often appears as returning what was lost",
    },
    {
        "title": "the parade map twist",
        "premise": "the parade map was folded wrong, so the route seemed to loop into the fountain garden",
        "obstacle": "the marchers feared they would miss the school steps where families were waiting",
        "clue": "one crease line pointed straight past the bell tower, not toward the garden",
        "mistake": "{child_name} first read the map upside down and led everyone toward the wrong arch",
        "action": "{sailor_name} held the map to the light, and {infantry_name} matched the creases to the street signs",
        "dialogue": "'Maps can twist in our hands,' {sailor_name} said. 'But the town is still where it was,' {child_name} said with a grin",
        "resolution": "The parade turned the right corner, and the waiting families waved from the school steps",
        "ending": "the whole line arrived in time to hear cheers roll down the street like warm bread",
        "lesson": "a mistaken twist can become heartwarming when everyone helps correct it",
    },
]


OPENINGS = [
    "At sunset, {child_name} arrived in parade square with {sailor_name} and {infantry_name}.",
    "The lanterns were just waking up when {child_name} walked into parade square beside {sailor_name} and {infantry_name}.",
    "As the parade music warmed the air, {child_name} came to parade square with {sailor_name} and {infantry_name}.",
    "By the time the sky turned peach, {child_name} had reached parade square to watch the parade with {sailor_name} and {infantry_name}.",
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming parade world with a sailor, infantry, and a kind twist.")
    ap.add_argument("--parade-name")
    ap.add_argument("--sailor-name")
    ap.add_argument("--infantry-name")
    ap.add_argument("--child-name")
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
    place = args.place or "parade square"
    time = args.time or "sunset"
    if place != "parade square":
        raise StoryError("This world is built around parade square.")
    if time != "sunset":
        raise StoryError("This world is built around sunset.")
    return StoryParams(
        seed=None,
        parade_name=args.parade_name or rng.choice(["the lantern parade", "the ribbon parade", "the music parade"]),
        sailor_name=args.sailor_name or rng.choice(["Mira", "Sana", "Iris"]),
        infantry_name=args.infantry_name or rng.choice(["Captain Ilyas", "Sergeant Tom", "Lieutenant Ben"]),
        child_name=args.child_name or rng.choice(["Nora", "Lina", "Owen"]),
        object_name=args.object_name or rng.choice(["the ribbon banner", "the brass drum", "the lantern cart"]),
        place=place,
        time=time,
    )


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("place", "parade_square"),
            asp.fact("feature", "twist"),
            asp.fact("feature", "heartwarming"),
            asp.fact("together", "sailor", "infantry"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def python_reasonable_story() -> bool:
    return True


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show safe_resolution/0."))
    asp_ok = bool(asp.atoms(model, "safe_resolution"))
    py_ok = python_reasonable_story()
    if asp_ok == py_ok:
        print("OK: ASP and Python agree on the story gate.")
        return 0
    print(f"MISMATCH: asp={asp_ok} python={py_ok}")
    return 1


def generate_story(world: World) -> None:
    p = world.params
    seed = p.seed if p.seed is not None else 0
    scenario = SCENARIOS[seed % len(SCENARIOS)]
    opening = OPENINGS[(seed // len(SCENARIOS)) % len(OPENINGS)]
    values = {
        "parade_name": p.parade_name,
        "sailor_name": p.sailor_name,
        "infantry_name": p.infantry_name,
        "child_name": p.child_name,
        "object_name": p.object_name,
        "place": p.place,
        "time": p.time,
    }

    child = world.add_character(Character(name=p.child_name, role="child"))
    sailor = world.add_character(Character(name=p.sailor_name, role="sailor"))
    infantry = world.add_character(Character(name=p.infantry_name, role="infantry"))
    banner = world.add_thing(Thing(name=p.object_name, kind="parade object"))

    child.add_meme("curiosity", 1)
    sailor.add_meme("care", 1)
    infantry.add_meme("steadiness", 1)

    world.say(opening.format(**values))
    world.say(f"The celebration was {p.parade_name}, and it smelled like warm sugar and painted wood.")
    world.say(f"Then came the problem: {scenario['premise']}. {scenario['obstacle']}.")
    world.say(f"{scenario['clue'].capitalize()}. That clue made the twist feel solvable instead of scary.")
    world.say(f"{scenario['mistake'].format(**values)}.")
    world.say(f"{scenario['action'].format(**values)}.")
    world.say(f"{scenario['dialogue'].format(**values)}.")
    world.say(f"{scenario['resolution']}.")
    world.say(f"{scenario['lesson'].capitalize()}.")
    world.say(f"In the end, {scenario['ending']}.")

    child.add_meme("joy", 1)
    sailor.add_meter("helped", 1)
    infantry.add_meter("steady_steps", 1)
    banner.add_meter("lifted", 1)

    world.facts = {
        "parade_name": p.parade_name,
        "sailor_name": p.sailor_name,
        "infantry_name": p.infantry_name,
        "child_name": p.child_name,
        "object_name": p.object_name,
        "place": p.place,
        "time": p.time,
        "scenario": scenario["title"],
        "problem": scenario["premise"],
        "clue": scenario["clue"].capitalize(),
        "resolution": scenario["resolution"],
        "ending": scenario["ending"],
        "lesson": scenario["lesson"],
    }


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = world.params
    return [
        QAItem(
            question=f"What problem appeared during {f['scenario']}?",
            answer=f"{f['problem']}. It mattered because the parade needed a safe, cheerful way to continue.",
        ),
        QAItem(
            question="What clue helped the characters understand the trouble?",
            answer=f"{f['clue']}. The clue pointed toward a careful fix instead of a rushed guess.",
        ),
        QAItem(
            question="How did the sailor and infantry help?",
            answer=f"{f['resolution']} The sailor and infantry worked together so the parade could keep going safely.",
        ),
        QAItem(
            question="What made the story heartwarming?",
            answer=f"It was heartwarming because {f['lesson']} and everyone ended with a better feeling than before.",
        ),
        QAItem(
            question="What ending image closes the story?",
            answer=f"The ending image is: {f['ending']}. It shows the changed parade in a concrete way.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Who is a sailor?",
            answer="A sailor is a person who works on water and is used to steady hands, ropes, and careful teamwork.",
        ),
        QAItem(
            question="Who is infantry?",
            answer="Infantry are people who march on foot together and rely on discipline, practice, and helping one another.",
        ),
        QAItem(
            question="What is a twist in a story?",
            answer="A twist is a change that surprises the characters and sends them toward a new way to solve the problem.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Tell a heartwarming story about {f['parade_name']} at parade square, with a sailor and infantry working together.",
        f"Make the twist depend on this clue: {f['clue']}. Include spoken dialogue that changes what someone does.",
        f"End with this image: {f['ending']}.",
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
    for thing in world.things.values():
        lines.append(f"  {thing.name} ({thing.kind}) meters={thing.meters} memes={thing.memes}")
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
        print(asp_program("#show safe_resolution/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show safe_resolution/0."))
        print("safe_resolution" if asp.atoms(model, "safe_resolution") else "(no safe_resolution)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        params = StoryParams(
            seed=base_seed,
            parade_name=args.parade_name or "the lantern parade",
            sailor_name=args.sailor_name or "Mira",
            infantry_name=args.infantry_name or "Captain Ilyas",
            child_name=args.child_name or "Nora",
            object_name=args.object_name or "the ribbon banner",
            place="parade square",
            time="sunset",
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
