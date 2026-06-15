"""
gen6k09.py - Data01 coverage/quality push for gen6.

Sampled from the highest-frequency missing names on data01 after gen6k08. These
kernels favor embedded carrier state and phase preservation: structural calls
route through meta_story, character-focused states update meme magnitudes, and
plain physical actions avoid the generic fallback wording.
"""

from __future__ import annotations

from typing import Any

from gen6 import REGISTRY, World, Entity, NLGUtils, coherent, is_meta_call, meta_story, to_phrase
from gen6k03 import _split, _cap
from gen6k07 import _actor_from, _clean_sentence, _concepts, _kw_values, _sentences
from gen6k08 import _register_action, _register_meta, _register_state


def _target(chars: list[Entity], rest: list[Any], kw: dict, *keys: str) -> str:
    return _concepts(list(chars) + rest + _kw_values(kw, *keys))


def _participants(chars: list[Entity], rest: list[Any], kw: dict) -> list[Entity]:
    out = list(chars)
    for key in ("participants", "Participants", "actors", "group"):
        value = kw.get(key)
        if isinstance(value, Entity):
            out.append(value)
        elif isinstance(value, (list, tuple)):
            out.extend(v for v in value if isinstance(v, Entity))
    return out


def _group_subject(ctx: World, chars: list[Entity], rest: list[Any], kw: dict) -> tuple[Entity | None, str]:
    parts = _participants(chars, rest, kw)
    if parts:
        ctx.actor = parts[0]
        return parts[0], NLGUtils.join_list([str(p) for p in parts])
    actor = _actor_from(ctx, chars, kw)
    return actor, ctx.say(actor) if actor is not None else "Everyone"


@REGISTRY.kernel("Show")
def Show(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    if not chars and len(rest) >= 2:
        subject = _concepts([rest[0]] + _kw_values(kw, "subject", "item", "object"))
        audience = _concepts([rest[1]] + _kw_values(kw, "to", "audience"))
    else:
        audience = _target(chars[1:], [], kw, "to", "audience")
        subject = _target([], rest, kw, "subject", "item", "object")
    sents = _sentences(rest + list(kw.values()))
    if actor is not None:
        actor.add_meme("Expression", 0.3)
        ctx.actor = actor
        tail = f" {subject}" if subject else " something"
        if audience:
            tail += f" to {audience}"
        lead = f"{ctx.say(actor)} showed{tail}."
        return coherent(ctx, actor, [lead] + sents)
    return " ".join(sents) if sents else f"Someone showed {subject}."


@REGISTRY.kernel("Lost")
def Lost(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else None
    thing = _target(chars[1:], rest, kw, "item", "object", "thing")
    place = _concepts(_kw_values(kw, "place", "location"))
    if actor is not None:
        actor.add_meme("Fear", 0.3)
        ctx.actor = actor
        where = f" in {place}" if place else ""
        return f"{ctx.say(actor)} got lost{where}."
    carrier = ctx.actor
    if carrier is not None:
        carrier.add_meme("Loss", 0.4)
    return f"{_cap(thing)} was lost." if thing else "Something was lost."


@REGISTRY.kernel("Harmony")
def Harmony(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    names = NLGUtils.join_list([str(c) for c in chars])
    ideas = _target([], rest, kw, "between", "with")
    actor = chars[0] if chars else ctx.actor
    if actor is not None:
        actor.add_meme("Friendship", 0.5)
        ctx.actor = actor
    subject = names or ideas or "Everyone"
    return f"{subject} found harmony together."


@REGISTRY.kernel("Empathy")
def Empathy(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    target = _target(chars[1:], rest, kw, "target", "for")
    if actor is not None:
        actor.add_meme("Kindness", 0.4)
        actor.add_meme("Understanding", 0.4)
        ctx.actor = actor
        return f"{ctx.say(actor)} understood how {target} felt." if target else f"{ctx.say(actor)} showed empathy."
    return f"Everyone showed empathy for {target}." if target else "Everyone showed empathy."


@REGISTRY.kernel("Party")
def Party(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor, subject = _group_subject(ctx, chars, rest, kw)
    if actor is not None:
        actor.add_meme("Joy", 0.5)
    body = meta_story(ctx, actor, kw) if actor is not None and is_meta_call(kw) else ""
    sents = _sentences(rest)
    lead = f"{subject} had a party."
    return coherent(ctx, actor, [lead, body] + sents)


@REGISTRY.kernel("Playground")
def Playground(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor, subject = _group_subject(ctx, chars, rest, kw)
    if actor is not None:
        actor.add_meme("Joy", 0.4)
    body = meta_story(ctx, actor, kw) if actor is not None and is_meta_call(kw) else ""
    sents = _sentences(rest)
    lead = f"{subject} played at the playground."
    return coherent(ctx, actor, [lead, body] + sents)


@REGISTRY.kernel("Music")
def Music(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    source = _target(chars[1:], rest, kw, "source")
    if actor is not None:
        actor.add_meme("Joy", 0.3)
        ctx.actor = actor
        return f"{ctx.say(actor)} heard music from {source}." if source else f"{ctx.say(actor)} heard music."
    return f"Music came from {source}." if source else "Music began to play."


@REGISTRY.kernel("Sunset")
def Sunset(ctx: World, *args: Any, **kw: Any) -> str:
    colors = _target([], list(args), kw, "sky", "color")
    return f"The sunset glowed with {colors}." if colors else "The sunset glowed."


@REGISTRY.kernel("Letter")
def Letter(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    target = _target(chars[1:], rest, kw, "sender", "receiver", "to", "about")
    if actor is not None:
        actor.add_meme("Communication", 0.3)
        ctx.actor = actor
        return f"{ctx.say(actor)} had a letter about {target}." if target else f"{ctx.say(actor)} had a letter."
    return f"There was a letter about {target}." if target else "There was a letter."


@REGISTRY.kernel("Icecream")
def Icecream(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    flavor = _target(chars[1:], rest, kw, "flavor")
    if actor is not None:
        actor.add_meme("Joy", 0.3)
        ctx.actor = actor
        return f"{ctx.say(actor)} enjoyed ice cream with {flavor}." if flavor else f"{ctx.say(actor)} enjoyed ice cream."
    return f"There was {flavor} ice cream." if flavor else "There was ice cream."


@REGISTRY.kernel("Showcase")
def Showcase(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    presenter = _concepts(_kw_values(kw, "presenter")) or (ctx.say(actor) if actor else "Someone")
    subject = _target(chars[1:], rest, kw, "subject", "props")
    body = meta_story(ctx, actor, kw) if actor is not None and is_meta_call(kw) else ""
    lead = f"{presenter} showcased {subject}." if subject else f"{presenter} put on a showcase."
    return coherent(ctx, actor, [lead, body])


@REGISTRY.kernel("Idea")
def IdeaTolerant(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    sents = _sentences(rest + list(kw.values()))
    topic = _target(chars[1:], rest, kw, "plan", "goal", "to", "help")
    if actor is not None:
        actor.add_meme("Creativity", 0.4)
        actor.add_meme("Joy", 0.2)
        ctx.actor = actor
        lead = f"{ctx.say(actor)} had a clever idea"
        lead += f" about {topic}." if topic else "."
        return coherent(ctx, actor, [lead] + sents)
    return " ".join(sents) if sents else "Someone had a clever idea."


@REGISTRY.kernel("balanced")
def balanced_lower(ctx: World, *args: Any, **kw: Any) -> str:
    chars, rest = _split(args)
    actor = _actor_from(ctx, chars, kw)
    target = _target(chars[1:], rest, kw, "activity", "between")
    if actor is not None:
        actor.add_meme("Balance", 1.0)
        ctx.actor = actor
        return f"{ctx.say(actor)} found balance with {target}." if target else f"{ctx.say(actor)} found balance."
    return f"There was balance with {target}." if target else "There was balance."


@REGISTRY.kernel("balance")
def balance_lower(ctx: World, *args: Any, **kw: Any) -> str:
    target = _target([], list(args), kw, "activity", "between")
    return f"balance with {target}" if target else "balance"


@REGISTRY.kernel("lesson")
def lesson_lower(ctx: World, *args: Any, **kw: Any) -> str:
    topic = NLGUtils.join_list([to_phrase(v) for v in list(args) + _kw_values(kw, "about", "moral") if to_phrase(v)])
    return f"the importance of {topic}" if topic else "an important lesson"


for _name, _template, _meme in [
    ("Envy", "{s} felt envy toward {t}.", "Envy"),
    ("Shock", "{s} was shocked by {t}.", "Fear"),
    ("Alarm", "{s} felt alarm about {t}.", "Fear"),
    ("Itch", "{s} had an itch from {t}.", "Discomfort"),
    ("Trouble", "{s} faced trouble with {t}.", "Problem"),
    ("Cozy", "{s} felt cozy with {t}.", "Comfort"),
    ("Under", "{s} was under {t}.", "Place"),
    ("Prize", "{s} won a prize for {t}.", "Reward"),
    ("Exclusion", "{s} felt excluded from {t}.", "Sadness"),
    ("Shade", "{s} rested in the shade of {t}.", "Comfort"),
    ("Confident", "{s} felt confident about {t}.", "Confidence"),
    ("Face", "{s} made a face about {t}.", "Expression"),
    ("Real", "{s} realized {t} was real.", "Awareness"),
    ("Sweet", "{s} found {t} sweet.", "Joy"),
    ("Resourceful", "{s} was resourceful with {t}.", "Creativity"),
    ("Greed", "{s} felt greedy about {t}.", "Desire"),
    ("Unhappy", "{s} was unhappy about {t}.", "Sadness"),
    ("Fame", "{s} became known for {t}.", "Recognition"),
    ("Independence", "{s} gained independence with {t}.", "Confidence"),
    ("Emergence", "{s} saw {t} emerge.", "Awareness"),
    ("Festival", "{s} enjoyed a festival with {t}.", "Joy"),
    ("Persistent", "{s} stayed persistent with {t}.", "Persistence"),
    ("Honesty", "{s} chose honesty about {t}.", "Truth"),
    ("Pretty", "{s} looked pretty with {t}.", "Beauty"),
    ("Aftermath", "{s} faced the aftermath of {t}.", "Consequence"),
    ("Grateful", "{s} felt grateful for {t}.", "Gratitude"),
    ("Soft", "{s} felt soft around {t}.", "Comfort"),
    ("Loved", "{s} felt loved by {t}.", "Love"),
    ("Size", "{s} noticed the size of {t}.", "Awareness"),
    ("Alliance", "{s} formed an alliance with {t}.", "Friendship"),
    ("Gust", "{s} felt a gust from {t}.", "Weather"),
    ("Restraint", "{s} showed restraint with {t}.", "Restraint"),
    ("Incentive", "{s} had an incentive for {t}.", "Motivation"),
    ("Aversion", "{s} felt aversion to {t}.", "Disgust"),
    ("Caregiving", "{s} gave care to {t}.", "Care"),
    ("JoyfulCreation", "{s} joyfully created {t}.", "Joy"),
    ("Forest", "{s} was in the forest with {t}.", "Place"),
    ("Judgment", "{s} made a judgment about {t}.", "Judgment"),
    ("Closed", "{s} was closed off from {t}.", "Closure"),
    ("Glad", "{s} felt glad about {t}.", "Joy"),
    ("Dirt", "{s} noticed dirt on {t}.", "Mess"),
    ("Mishap", "{s} had a mishap with {t}.", "Accident"),
] :
    _register_state(_name, _template, meme=_meme)


for _name, _past, _solo, _meme in [
    ("Roll", "rolled", "along", "Movement"),
    ("Keep", "kept", "it", "Possession"),
    ("Dress", "dressed", "up", "Care"),
    ("Shake", "shook", "it", "Movement"),
    ("Spin", "spun", "around", "Movement"),
    ("Repeat", "repeated", "it", "Practice"),
    ("Work", "worked on", "it", "Effort"),
    ("Serve", "served", "something", "Care"),
    ("Lock", "locked", "it", "Safety"),
    ("Mail", "mailed", "a letter", "Communication"),
    ("Fit", "fit", "perfectly", "Completion"),
    ("Poke", "poked", "it", "Curiosity"),
    ("Whisper", "whispered about", "it", "Communication"),
    ("Point", "pointed at", "it", "Attention"),
    ("Peek", "peeked at", "it", "Curiosity"),
    ("Brush", "brushed", "it", "Care"),
    ("Freeze", "froze near", "it", "Cold"),
    ("Stack", "stacked", "things", "Building"),
    ("Soar", "soared over", "the sky", "Flight"),
    ("Board", "boarded", "it", "Journey"),
    ("Glue", "glued", "it", "Repair"),
    ("Rise", "rose above", "it", "Movement"),
    ("Lean", "leaned on", "it", "Rest"),
    ("Discuss", "discussed", "it", "Communication"),
    ("Improve", "improved", "it", "Growth"),
    ("StepOn", "stepped on", "it", "Mistake"),
    ("Attend", "attended", "it", "Presence"),
    ("Investigate", "investigated", "it", "Curiosity"),
    ("Befriend", "befriended", "someone", "Friendship"),
    ("Demonstrate", "demonstrated", "it", "Teaching"),
    ("Applaud", "applauded", "warmly", "Joy"),
    ("KeepClose", "kept close", "someone", "Safety"),
    ("Snatch", "snatched", "something", "Theft"),
    ("Strengthen", "strengthened", "it", "Strength"),
    ("Persuade", "persuaded", "someone", "Communication"),
    ("Anticipate", "anticipated", "what came next", "Anticipation"),
    ("Flee", "fled from", "danger", "Fear"),
    ("PutBack", "put back", "it", "Order"),
    ("Disturb", "disturbed", "someone", "Disruption"),
    ("Haircut", "gave a haircut to", "someone", "Care"),
    ("Nod", "nodded to", "someone", "Agreement"),
    ("Sting", "stung", "someone", "Pain"),
    ("Expect", "expected", "it", "Anticipation"),
    ("Discard", "discarded", "it", "Loss"),
    ("Stare", "stared at", "it", "Attention"),
    ("Sink", "sank into", "it", "Danger"),
    ("Scrape", "scraped", "it", "Pain"),
    ("Summon", "summoned", "someone", "Call"),
    ("Increase", "increased", "it", "Growth"),
    ("Pile", "piled up", "things", "Collection"),
    ("Decide", "decided about", "it", "Choice"),
    ("Chop", "chopped", "it", "Action"),
    ("Cease", "stopped", "it", "Ending"),
    ("Intervene", "intervened in", "it", "Help"),
    ("Hint", "hinted about", "it", "Communication"),
    ("Awake", "woke up", "again", "Awareness"),
    ("Contain", "contained", "it", "Safety"),
    ("Peck", "pecked at", "it", "Action"),
    ("Untie", "untied", "it", "Freedom"),
] :
    _register_action(_name, _past, solo=_solo, meme=_meme)


for _name, _fallback, _meme in [
    ("Parade", "{s} joined a parade", "Joy"),
    ("Gathering", "{s} joined a gathering", "Community"),
    ("Playdate", "{s} had a playdate", "Friendship"),
    ("CreativePlay", "{s} played creatively", "Creativity"),
    ("BeachVisit", "{s} visited the beach", "Joy"),
] :
    _register_meta(_name, _fallback, meme=_meme)


if __name__ == "__main__":
    import gen6registry  # noqa: F401
    from gen6 import generate

    tests = [
        "Amy(Character, girl)\nTim(Character, boy)\nShow(Amy, Tim, Organize(dolls))",
        "Timmy(Character, boy)\nLost(Timmy, place=maze)",
        "Lily(Character, girl)\nPlayground(participants=[Lily], process=Spin(toyTop) + Sunset())",
        "Jack(Character, boy)\nLie(Jack, claim=No) + Honesty(Jack)",
    ]
    for i, test in enumerate(tests, 1):
        print(f"--- TEST {i} ---")
        print(generate(test))
        print()
