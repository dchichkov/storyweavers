#!/usr/bin/env python3
"""Gingham Magic: a nursery-rhyme world of small problems and bright fixes."""

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
    kind: str
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


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
    hero: str = "Mabel"
    friend: str = "Pip"
    problem: str = "moon"
    solution: str = "lantern"
    companion: str = "mouse"
    verse: str = "lilting"
    seed: int = 777


NAMES = ("Mabel", "Pip", "Nell", "Toby", "Rae", "Kit")
COMPANIONS = ("mouse", "robin", "lamb")
VERSES = ("lilting", "bouncy", "tender")

PROBLEMS = {
    "moon": "the moon has slipped from the sky",
    "bell": "the nursery bell has lost its ring",
    "rain": "rain is dripping through the gingham tent",
    "shadow": "a shadow is hiding the path home",
}
SOLUTIONS = {
    "lantern": "light",
    "ribbon": "tie",
    "thimble": "mend",
    "song": "sing",
}
COMPATIBLE = {
    "moon": ("lantern", "ribbon"),
    "bell": ("song", "thimble"),
    "rain": ("ribbon", "thimble"),
    "shadow": ("lantern", "song"),
}

PROMPT = "Write a dialogue-rich nursery-rhyme story about gingham, magic, and a small problem solved by friends."


class World:
    def __init__(self, params: StoryParams):
        self.params = params
        self.entities: dict[str, Entity] = {
            "hero": Entity("hero", params.hero, "character", "gingham meadow",
                           memes={"courage": 0.5, "trust": 0.5}),
            "friend": Entity("friend", params.friend, "character", "gingham meadow",
                             memes={"courage": 0.5, "trust": 0.5}),
            "companion": Entity("companion", f"the {params.companion}", "animal",
                                "gingham meadow", memes={"helpfulness": 0.7}),
            "magic": Entity("magic", "the magic", "force", "gingham meadow",
                            meters={"strength": 1.0}),
        }
        self.history: list[Event] = []

    def snapshot(self) -> dict:
        return {key: asdict(value) for key, value in self.entities.items()}

    def narrate(self, kind: str, text: str, *, question: str = "",
                cause: str = "", result: str = "") -> None:
        self.history.append(Event(kind=kind, text=text, question=question,
                                  cause=cause, result=result, state=self.snapshot()))

    def say(self, who: str, text: str, *, to: str = "", reveal: str = "",
            tag: str = "said") -> None:
        if who not in self.entities:
            raise StoryError("A story speaker is missing.")
        if text.endswith("?") and tag == "said":
            tag = "asked"
        self.history.append(Event(
            kind="speech",
            text=f'"{text}" {self.entities[who].label} {tag}.',
            speaker=who, listener=to, revealed=reveal, state=self.snapshot()))

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
                QAItem("What cloth runs through this magical world?",
                        "Gingham cloth appears in the meadow, tent, and moon-patch."),
                QAItem("What makes the magic work?",
                        "A clear wish joined to a useful action makes the magic work."),
            ],
            world=self,
        )


def validate_params(params: StoryParams) -> None:
    if params.problem not in PROBLEMS:
        raise StoryError("Choose a known nursery problem.")
    if params.solution not in SOLUTIONS:
        raise StoryError("Choose a known magical solution.")
    if params.solution not in COMPATIBLE[params.problem]:
        raise StoryError(f"{params.solution!r} cannot solve {params.problem!r}.")
    if params.companion not in COMPANIONS or params.verse not in VERSES:
        raise StoryError("Choose a known companion and verse.")
    if params.hero == params.friend:
        raise StoryError("The two speakers need different names.")
    if any(not re.fullmatch(r"[A-Z][a-z]+", name)
           for name in (params.hero, params.friend)):
        raise StoryError("Names must be simple capitalized words.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    world = World(params)
    world.entities["gingham"] = Entity(
        "gingham", "the red-and-white gingham", "cloth", "gingham meadow",
        meters={"dryness": 0.8, "strength": 1.0})
    world.entities["moon"] = Entity(
        "moon", "the moon", "sky-object", "sky", meters={"height": 5, "glow": 1})
    world.entities["bell"] = Entity(
        "bell", "the nursery bell", "instrument", "gingham meadow",
        meters={"ring": 0})
    world.entities["tent"] = Entity(
        "tent", "the gingham tent", "shelter", "gingham meadow",
        meters={"holes": 2, "dry": 0})
    world.entities["path"] = Entity(
        "path", "the silver path", "path", "gingham meadow",
        meters={"visible": 0})
    return world


def finish_world(world: World) -> None:
    for key in ("hero", "friend"):
        world.entities[key].memes["trust"] = 1.0
        world.entities[key].memes["courage"] = 1.0


def moon_story(world: World) -> None:
    p = world.params
    h, f = p.hero, p.friend
    world.narrate(
        "beginning",
        f"In a gingham meadow, beneath a lavender tree, {h} and {f} danced a "
        f"small {p.verse} tune. But the moon slipped down with a silvery swoon.")
    world.say("hero", "The moon is in the grass! How shall the night be bright?")
    world.say("friend", "I thought magic meant waiting for wishes to do the work.")
    world.narrate(
        "problem",
        f"The moon lay in a puddle, dim as a button, while the gingham meadow "
        f"lost its light.",
        question="Why did the meadow grow dark?",
        cause="The moon had slipped from the sky into the grass.",
        result="Its dim glow could no longer light the meadow.")
    if p.solution == "lantern":
        world.say("hero", "Let us place it in a lantern and lift it with care.")
        world.say("friend", "A lantern can hold a glow, but we must carry it together.")
        world.entities["moon"].location = "lantern"
        world.entities["moon"].meters.update(height=5, glow=1)
        world.entities["magic"].meters["strength"] += 1
        world.narrate(
            "turn",
            f"{h} opened a starry lantern. {f} cupped the moon inside, and the "
            f"lantern rose on a gingham ribbon.",
            question="How did the friends return light to the meadow?",
            cause=f"{h} suggested a lantern, and {f} helped carry the moon safely.",
            result="The moon glowed inside a lantern and rose above the meadow.")
        world.say("hero", "Up you go, little moon!")
        world.say("friend", "And now the lantern shows us where the sky begins.")
        world.entities["moon"].location = "sky"
    else:
        world.say("hero", "A ribbon can guide it back to its place.")
        world.say("friend", "Then I will tie the ribbon, while you pull the moon.")
        world.entities["moon"].location = "gingham ribbon"
        world.entities["moon"].meters.update(height=5, glow=1)
        world.narrate(
            "turn",
            f"{f} tied a gingham ribbon around the moon's silver edge. {h} pulled "
            f"gently, and the moon climbed the ribbon to the sky.",
            question="How did the friends guide the moon upward?",
            cause="They used a gingham ribbon as a gentle guide instead of pulling the moon roughly.",
            result="The moon climbed the ribbon and returned to the sky.")
        world.say("hero", "The ribbon is a road for moonlight.")
        world.say("friend", "And the sky is smiling at our tidy work.")
        world.entities["moon"].location = "sky"
    finish_world(world)
    world.narrate(
        "ending",
        f"The moon shone round and bright. The gingham meadow glittered, and {h} "
        f"and {f} twirled beneath its silver light.",
        question="What changed at the end of the moon adventure?",
        cause="The friends used a useful action with their wish instead of waiting passively.",
        result="The moon returned to the sky and lit the gingham meadow again.")


def bell_story(world: World) -> None:
    p = world.params
    h, f = p.hero, p.friend
    world.narrate(
        "beginning",
        f"At noon in the gingham nursery, {h} polished the bell while {f} "
        f"counted blue buttons. The bell gave no ring at all.")
    world.say("hero", "The bell is mute. Shall we shout its sound for it?")
    world.say("friend", "A shout is loud, but it will not mend a broken clapper.")
    world.narrate(
        "problem",
        "The nursery bell swung back and forth, but its little tongue was still.",
        question="Why did the nursery bell stay silent?",
        cause="The bell's clapper was broken, so swinging it made no sound.",
        result="The children needed to discover whether to sing or mend.")
    if p.solution == "song":
        world.say("hero", "Let us sing the bell's name and wake its magic.")
        world.say("friend", "I know the tune. Follow my bright high note.")
        world.entities["bell"].meters["ring"] = 1
        world.entities["magic"].meters["strength"] += 1
        world.narrate(
            "turn",
            f"{h} sang ding-dong-ding, and {f} joined with a clear little hum. "
            "The silent bell borrowed their tune and began to ring.",
            question="How did the friends wake the silent bell?",
            cause="The friend knew a bell-like tune, and both children sang it together.",
            result="The magic carried their song into a real bell ring.")
        world.say("hero", "It heard us!")
        world.say("friend", "Sometimes a song can show a thing how to begin.")
    else:
        world.say("hero", "The clapper is cracked. My thimble can hold it fast.")
        world.say("friend", "I will hold the bell steady while you mend it.")
        world.entities["bell"].meters["ring"] = 1
        world.entities["magic"].meters["strength"] += 1
        world.narrate(
            "turn",
            f"{f} steadied the bell, while {h} used a silver thimble to mend its "
            "tiny clapper. Ding! went the bell.",
            question="How did the friends repair the bell?",
            cause="The friend held the bell steady while the hero used a thimble to mend its clapper.",
            result="The repaired clapper struck the bell and made it ring.")
        world.say("hero", "A thimble is small, but a small tool can do a large job.")
        world.say("friend", "And a steady hand makes magic safer.")
    finish_world(world)
    world.narrate(
        "ending",
        f"Ding-dong, ding-dong! The gingham curtains danced as {h} and {f} "
        "rang the nursery into its afternoon nap.",
        question="What proved that the bell was fixed?",
        cause="The friends either joined a magical tune or repaired the clapper.",
        result="The bell rang clearly while the gingham curtains danced.")


def rain_story(world: World) -> None:
    p = world.params
    h, f = p.hero, p.friend
    world.narrate(
        "beginning",
        f"Rain tapped the gingham tent: tip-tap, tip-tap. {h} held a cup beneath "
        f"a drip, while {f} watched the puddle grow.")
    world.say("hero", "The tent is leaking. Shall we carry it away?")
    world.say("friend", "It is our shelter, not a blanket to drag through mud.")
    world.narrate(
        "problem",
        "Two holes opened above the little table, and raindrops fell on the tea.",
        question="Why did the tea table get wet?",
        cause="Two holes had opened in the gingham tent.",
        result="Rain fell through the cloth onto the table.")
    if p.solution == "ribbon":
        world.say("hero", "We can tie the loose cloth with a ribbon.")
        world.say("friend", "I will pull the corners close while you make the bow.")
        world.entities["tent"].meters.update(holes=0, dry=1)
        world.entities["gingham"].meters["dryness"] = 1
        world.narrate(
            "turn",
            f"{h} drew the gingham corners together, and {f} tied them with a "
            "blue ribbon. The rain slid around the neat bow.",
            question="How did the friends stop the rain?",
            cause="They pulled the loose gingham corners together and tied them with a ribbon.",
            result="The holes closed, so rain slid around the tent instead of through it.")
        world.say("hero", "The bow is a tiny roof beam.")
        world.say("friend", "Then our tea may stay warm and dry.")
    else:
        world.say("hero", "My thimble can stitch the holes shut.")
        world.say("friend", "I will count each stitch so none is missed.")
        world.entities["tent"].meters.update(holes=0, dry=1)
        world.entities["gingham"].meters["dryness"] = 1
        world.narrate(
            "turn",
            f"{h} stitched the gingham with a silver thimble while {f} counted: "
            "one, two, three. The rain could find no doorway.",
            question="How did the friends mend the tent?",
            cause="The friend counted carefully while the hero stitched both holes with a thimble.",
            result="The gingham became whole and kept the tea table dry.")
        world.say("hero", "The last stitch is snug.")
        world.say("friend", "And every raindrop must seek another roof.")
    finish_world(world)
    world.narrate(
        "ending",
        f"Tip-tap outside, sip-sip inside. The gingham tent stood dry, and {h} "
        f"and {f} shared their tea beneath its patched roof.",
        question="What showed that the shelter was safe again?",
        cause="The friends closed both holes with a ribbon or careful stitches.",
        result="The tea stayed dry while rain tapped outside.")


def shadow_story(world: World) -> None:
    p = world.params
    h, f = p.hero, p.friend
    world.narrate(
        "beginning",
        f"At dusk, a long shadow sprawled across the gingham meadow. {h} stopped "
        f"at the path, and {f} held a warm biscuit.")
    world.say("hero", "The shadow swallowed our path. I cannot tell where to step.")
    world.say("friend", "Perhaps it is not a monster. Perhaps it is only dark.")
    world.narrate(
        "problem",
        "The silver path vanished under the wide shadow of the lavender tree.",
        question="Why could the friends not find the way home?",
        cause="The tree's shadow covered the silver path at dusk.",
        result="The friends could not see where the safe stepping stones lay.")
    if p.solution == "lantern":
        world.say("hero", "A lantern can paint the path with gold.")
        world.say("friend", "I will carry it low, where the stones can shine.")
        world.entities["path"].meters["visible"] = 1
        world.narrate(
            "turn",
            f"{h} lit a magic lantern, and {f} carried it low. Gold squares "
            "appeared on the gingham path, one after another.",
            question="How did the friends reveal the hidden path?",
            cause="The friend carried a magic lantern low while the hero lit it.",
            result="Golden light showed each safe stone beneath the shadow.")
        world.say("hero", "There is the first stone!")
        world.say("friend", "And there is the next. We can walk by the light.")
    else:
        world.say("hero", "Let us sing a path into the dark.")
        world.say("friend", "I will sing when we reach a stone; you answer when it is safe.")
        world.entities["path"].meters["visible"] = 1
        world.narrate(
            "turn",
            f"{h} sang, " + '"Step by step,"' + f" and {f} answered, " +
            '"Home is near!" ' +
            "The magic song made silver stones sparkle beneath the shadow.",
            question="How did the friends follow the hidden path?",
            cause="They used a call-and-answer song to keep their steps together.",
            result="The magic song made the safe stones sparkle one by one.")
        world.say("hero", "Your song marks the next step.")
        world.say("friend", "And your answer tells me not to hurry.")
    finish_world(world)
    world.narrate(
        "ending",
        f"Home, home, hooray! The gingham door came into view, and {h} and {f} "
        "stepped inside with the shadow safely behind them.",
        question="What proved that the friends had found their way?",
        cause="They used light or a guiding song to reveal the safe stones.",
        result="They followed the silver path to the gingham door.")


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    if params.problem == "moon":
        moon_story(world)
    elif params.problem == "bell":
        bell_story(world)
    elif params.problem == "rain":
        rain_story(world)
    else:
        shadow_story(world)
    sample = world.sample()
    check_sample(sample)
    return sample


def check_sample(sample: StorySample) -> None:
    world = sample.world
    speech = [e for e in world.history if e.kind == "speech"]
    if len(speech) < 2:
        raise StoryError("The nursery rhyme needs a sustained exchange.")
    if not any(e.speaker == "hero" for e in speech) or not any(e.speaker == "friend" for e in speech):
        raise StoryError("Both characters must speak.")
    if not any(e.question for e in world.history):
        raise StoryError("The story needs grounded questions.")
    if any(not e.cause or not e.result for e in world.history if e.question):
        raise StoryError("Every story question needs a causal answer.")
    if any(world.entities[key].memes["trust"] < 1 for key in ("hero", "friend")):
        raise StoryError("The friends must finish trusting one another.")
    problem = world.params.problem
    if problem == "moon" and world.entities["moon"].location != "sky":
        raise StoryError("The moon must return to the sky.")
    if problem == "bell" and world.entities["bell"].meters["ring"] != 1:
        raise StoryError("The bell must ring.")
    if problem == "rain" and world.entities["tent"].meters["dry"] != 1:
        raise StoryError("The tent must become dry.")
    if problem == "shadow" and world.entities["path"].meters["visible"] != 1:
        raise StoryError("The path must become visible.")


ASP_RULES = """
problem(moon). problem(bell). problem(rain). problem(shadow).
solution(lantern,light). solution(ribbon,tie).
solution(thimble,mend). solution(song,sing).
works(moon,lantern). works(moon,ribbon).
works(bell,song). works(bell,thimble).
works(rain,ribbon). works(rain,thimble).
works(shadow,lantern). works(shadow,song).
valid(P,S) :- works(P,S).
#show valid/2.
"""


def asp_facts() -> str:
    from asp import fact
    lines = []
    for problem, solutions in COMPATIBLE.items():
        lines.append(fact("problem", problem))
        for solution in solutions:
            lines.append(fact("works", problem, solution))
    return "\n".join(lines)


def asp_combos() -> set[tuple[str, str]]:
    from asp import atoms, one_model
    return set(atoms(one_model(asp_facts() + "\n" + ASP_RULES), "valid"))


def valid_combos() -> list[tuple[str, str]]:
    return [(problem, solution)
            for problem, solutions in COMPATIBLE.items()
            for solution in solutions]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--hero")
    parser.add_argument("--friend")
    parser.add_argument("--problem", choices=tuple(PROBLEMS))
    parser.add_argument("--solution", choices=tuple(SOLUTIONS))
    parser.add_argument("--companion", choices=COMPANIONS)
    parser.add_argument("--verse", choices=VERSES)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        parser.add_argument("--" + flag, action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        pair for pair in valid_combos()
        if args.problem is None or pair[0] == args.problem
        if args.solution is None or pair[1] == args.solution
    ]
    if not choices:
        raise StoryError("That magical solution does not fit the selected problem.")
    problem, solution = rng.choice(choices)
    hero = args.hero or rng.choice([n for n in NAMES if n != args.friend])
    friend = args.friend or rng.choice([n for n in NAMES if n != hero])
    params = StoryParams(
        hero=hero,
        friend=friend,
        problem=problem,
        solution=solution,
        companion=args.companion or rng.choice(COMPANIONS),
        verse=args.verse or rng.choice(VERSES),
        seed=args.seed,
    )
    validate_params(params)
    return params


def verify() -> None:
    if set(valid_combos()) != asp_combos():
        raise StoryError("Python and ASP disagree about magical solutions.")
    count = 0
    for problem, solution in valid_combos():
        for companion in COMPANIONS:
            for verse in VERSES:
                sample = generate(StoryParams(
                    problem=problem, solution=solution,
                    companion=companion, verse=verse))
                check_sample(sample)
                count += 1
    print(f"OK: {count} story states; {len(valid_combos())} compatible paths.")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
            pairs = [
                pair for pair in valid_combos()
                if args.problem is None or pair[0] == args.problem
                if args.solution is None or pair[1] == args.solution
            ]
            if not pairs:
                raise StoryError("No compatible magical paths match these options.")
            params_list = []
            for problem, solution in pairs:
                copied = argparse.Namespace(**vars(args))
                copied.problem = problem
                copied.solution = solution
                params_list.append(resolve_params(copied, rng))
        else:
            params_list = [resolve_params(args, rng) for _ in range(args.n)]

        samples = [generate(params) for params in params_list]
        if args.json:
            payload = [sample.to_dict() for sample in samples]
            print(json.dumps(payload[0] if len(payload) == 1 else payload,
                             ensure_ascii=False, indent=2))
        else:
            for index, sample in enumerate(samples):
                emit(sample, trace=args.trace, qa=args.qa,
                     header=f"\n### Story {index + 1}\n"
                     if len(samples) > 1 else "")
        return 0
    except StoryError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
