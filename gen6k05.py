"""
gen6k05.py - Kernel Pack #05 for the gen6 engine.

Built by following the AGENTS.md gen6 workflow: the next ~90 highest-frequency
missing kernels (after gen6k04) were sampled from the dataset with a shape scan,
their real argument shapes studied, then implemented here.

Like gen6k03/gen6k04, this pack reuses the `transitive` / `intransitive` /
`emotion` / `event` factories from `gen6k03.py` for the simple verb/state kernels
and adds hand-written variants for the kernels whose real shapes need bespoke
rendering (group sharing, meta/multi-phase activities like Exploration / Creation
/ Illness / Choice / Task, object-first events like Missing / Broken / New, and
sensitive ones like Death / Injury / Grief).

Design notes (from the sampled shapes):
- Object-first calls with no leading character (`Reach(bowl)`, `Grow(tree)`,
  `Go(park)`) attach to the current protagonist when present, else read as a
  subjectless sentence.
- Phase kwargs (`state=`, `process=`, `outcome=`, ...) route to `meta_story` so a
  "simple" kernel called richly still tells a full story.
"""

from __future__ import annotations

from typing import Any

from gen6 import (
    REGISTRY,
    World,
    Entity,
    Trace,
    NLGUtils,
    to_phrase,
    state_to_phrase,
    action_to_phrase,
    child_sentences,
    coherent,
    meta_story,
    is_meta_call,
    _lead_join,
)

from gen6k03 import (
    transitive,
    intransitive,
    emotion,
    event,
    _split,
    _phrases,
    _kw_targets,
    _cap,
    _is_char,
)

# Reuse gen6k04's group-cooperation renderer for the `Cooperate` synonym.
from gen6k04 import Collaboration as _Collaboration


def _register(name: str, fn) -> None:
    fn.__name__ = name
    REGISTRY.kernel(name)(fn)


def _vals(kw: dict, *keys: str):
    for k in keys:
        if k in kw and kw[k] is not None:
            return kw[k]
    return None


def _bare(phrase: str) -> str:
    """Strip a leading article so it can be re-articled (``the car seat`` ->
    ``car seat``); lowercase undefined names arrive as objects like "the car"."""
    low = phrase.lower()
    for a in ("the ", "a ", "an "):
        if low.startswith(a):
            return phrase[len(a):]
    return phrase


def _child_sents(values):
    """Collect child-Trace sentences from an iterable of values (skip Nones)."""
    out = []
    for v in values:
        if v is None:
            continue
        cs = child_sentences(v)
        if cs is not None:
            out += cs
    return out


# ---------------------------------------------------------------------------
# Simple transitive verbs (subject `past` object[s]; meta-aware via the factory)
# ---------------------------------------------------------------------------

transitive("Reach", "reached for", solo="out")
transitive("Grab", "grabbed", solo="it")
transitive("Bite", "bit", solo="it")
transitive("Avoid", "stayed away from", solo="trouble")
transitive("Feed", "fed", solo="the animals", love=0.2)
transitive("Purchase", "bought", solo="something", joy=0.2)
transitive("Capture", "caught", solo="it")
transitive("Paint", "painted", solo="a picture", joy=0.2, pride=0.2)
transitive("Kick", "kicked", solo="the ball")
transitive("Approach", "went up to", solo="closer")
transitive("Drive", "drove", solo="around")
transitive("Check", "checked", solo="everything")
transitive("Tell", "told", solo="everyone")
transitive("Put", "put down", solo="it away")
transitive("Lift", "lifted", solo="it up")
transitive("Count", "counted", solo="them all")
transitive("Move", "moved", solo="it")
transitive("Add", "added", solo="some more")
transitive("Dig", "dug", solo="a hole")
transitive("Fill", "filled", solo="it up")
transitive("Remove", "took away", solo="it")
transitive("Scare", "scared", solo="everyone")
transitive("Receive", "received", solo="a gift", joy=0.3)
transitive("Answer", "answered", solo="the question")
transitive("Choose", "chose", solo="one")
transitive("Stop", "stopped", solo="right there")
transitive("Reject", "turned down", solo="it")
transitive("Grant", "granted", solo="the wish", love=0.2)
transitive("Write", "wrote", solo="a story", wisdom=0.1)
transitive("Hear", "heard", solo="a sound")
transitive("Enjoy", "enjoyed", solo="every moment", joy=0.3)
transitive("Heal", "healed", solo="the hurt", love=0.2)
transitive("Respect", "respected", solo="everyone", love=0.2)
transitive("Leave", "left", solo="quietly")
transitive("Thanks", "thanked", solo="everyone", love=0.2)
transitive("Bonding", "bonded with", solo="everyone", love=0.3)
transitive("Reassurance", "reassured", solo="everyone", love=0.2)
transitive("Caution", "warned", solo="everyone")
transitive("Theft", "stole", solo="something")
transitive("Recall", "remembered", solo="everything", wisdom=0.1)
transitive("Claim", "claimed", solo="it")
transitive("Understanding", "understood", solo="everything", wisdom=0.3)
transitive("Inquiry", "asked about", solo="a question")


# ---------------------------------------------------------------------------
# Intransitive verbs (subject `past`; multiple chars share the subject)
# ---------------------------------------------------------------------------

intransitive("Grow", "grew", joy=0.1)
intransitive("Agree", "agreed")
intransitive("Swim", "swam", joy=0.2)
intransitive("Slip", "slipped", sadness=0.2)


# ---------------------------------------------------------------------------
# Emotions / states
# ---------------------------------------------------------------------------

emotion("Warm", "{s} felt warm and cozy.", meme="Joy", amount=0.3,
        solo="{s} was warm and cozy.")
emotion("Calm", "{s} felt calm.", meme="Relief", amount=0.3,
        solo="Everything felt calm and peaceful.")
emotion("Contentment", "{s} felt content.", meme="Joy", amount=0.4,
        solo="There was a feeling of contentment.")
emotion("Hunger", "{s} felt hungry.", solo="Everyone was getting hungry.")
emotion("Guilt", "{s} felt guilty.", meme="Sadness", amount=0.3,
        solo="There was a pang of guilt.")
emotion("Grief", "{s} was filled with grief.", meme="Sadness", amount=0.5,
        solo="There was deep grief.")
emotion("Upset", "{s} got upset.", meme="Sadness", amount=0.4,
        solo="Everyone was upset.")
emotion("Safe", "{s} was safe.", meme="Relief", amount=0.3,
        solo="It was safe and sound.")
emotion("Victory", "{s} had won!", meme="Pride", amount=0.5,
        solo="It was a great victory!")


# ---------------------------------------------------------------------------
# Object events (object-as-subject)
# ---------------------------------------------------------------------------

event("Broken", "was broken")


# ---------------------------------------------------------------------------
# Movement
# ---------------------------------------------------------------------------

def Go(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    dest = _vals(kw, "destination", "to")
    place = to_phrase(dest) if dest is not None else NLGUtils.join_list(_phrases(rest))
    movers = chars if chars else ([ctx.actor] if ctx.actor else [])
    if movers:
        for m in movers:
            m.add_meme("Joy", 0.1)
        ctx.actor = movers[0]
        subj = ctx.say(movers[0]) if len(movers) == 1 else NLGUtils.join_list([str(m) for m in movers])
        return f"{subj} went to {place}." if place else f"{subj} set off."
    return f"They went to {place}." if place else "Off they went."


# ---------------------------------------------------------------------------
# Sharing / group social
# ---------------------------------------------------------------------------

def Sharing(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    hero = chars[0] if chars else ctx.actor
    if hero is not None and is_meta_call(kw):
        for c in chars:
            c.add_meme("Friendship", 0.3)
        m = meta_story(ctx, hero, kw)
        if m:
            return m
    cs = _child_sents(rest)
    if cs:
        if hero is not None:
            ctx.actor = hero
        return coherent(ctx, hero, cs)
    items = NLGUtils.join_list(_phrases(rest) + _phrases([kw.get("items")] if kw.get("items") else []))
    with_who = kw.get("with")
    if hero is not None:
        ctx.actor = hero
        hero.add_meme("Love", 0.2)
        tail = f" with {to_phrase(with_who)}" if with_who is not None else ""
        return f"{ctx.say(hero)} shared {items}{tail}." if items else f"{ctx.say(hero)} shared with everyone."
    return f"Everyone shared {items}." if items else "There was lots of sharing."


# ---------------------------------------------------------------------------
# Meta / multi-phase activities
# ---------------------------------------------------------------------------

def Exploration(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    hero = chars[0] if chars else ctx.actor
    if hero is None and _is_char(kw.get("initiator")):
        hero = kw["initiator"]
    if hero is not None:
        ctx.actor = hero
        return meta_story(ctx, hero, kw, fallback=f"{hero.name} set off to explore.")
    place = NLGUtils.join_list(_phrases(rest))
    return f"There was so much to explore at {place}." if place else "There was so much to explore."


def Creation(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    hero = chars[0] if chars else ctx.actor
    if hero is not None:
        ctx.actor = hero
        hero.add_meme("Pride", 0.3)
        return meta_story(ctx, hero, kw, fallback=f"{hero.name} made something wonderful.")
    thing = NLGUtils.join_list(_phrases(rest))
    return f"{_cap(thing)} was created." if thing else "Something wonderful was created."


def Home(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    hero = chars[0] if chars else ctx.actor
    if hero is not None and is_meta_call(kw):
        ctx.actor = hero
        body = meta_story(ctx, hero, kw)
        return coherent(ctx, hero, [f"{ctx.say(hero)} was home."] + ([body] if body else []))
    if chars:
        ctx.actor = chars[0]
        return f"{NLGUtils.join_list([str(c) for c in chars])} went home."
    place = NLGUtils.join_list(_phrases(rest))
    return f"It was cozy at home by {place}." if place else "It was good to be home."


def Illness(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    hero = chars[0] if chars else ctx.actor
    if hero is not None and is_meta_call(kw):
        m = meta_story(ctx, hero, kw)
        if m:
            return m
    if hero is not None:
        ctx.actor = hero
        hero.add_meme("Sadness", 0.3)
        return f"{ctx.say(hero)} felt sick."
    thing = NLGUtils.join_list(_phrases(rest))
    return f"{_cap(thing)} fell ill." if thing else "An illness spread."


def Choice(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    hero = chars[0] if chars else ctx.actor
    if hero is not None and is_meta_call(kw):
        m = meta_story(ctx, hero, kw)
        if m:
            return m
    opts = NLGUtils.join_list(_phrases(rest) + _phrases([kw.get("options")] if kw.get("options") else []))
    if hero is not None:
        ctx.actor = hero
        return f"{ctx.say(hero)} chose {opts}." if opts else f"{ctx.say(hero)} made a choice."
    return f"There was a choice: {opts}." if opts else "A choice had to be made."


def Task(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    hero = chars[0] if chars else ctx.actor
    if hero is not None and is_meta_call(kw):
        m = meta_story(ctx, hero, kw)
        if m:
            return m
    sents = _child_sents(rest)
    if hero is not None:
        ctx.actor = hero
        if sents:
            return coherent(ctx, hero, [f"{ctx.say(hero)} had a job to do."] + sents)
        return f"{ctx.say(hero)} had a task to do."
    job = NLGUtils.join_list(_phrases(rest))
    return f"There was a task: {job}." if job else "There was a task to do."


# ---------------------------------------------------------------------------
# Cognition / communication
# ---------------------------------------------------------------------------

def Reaction(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    hero = chars[0] if chars else ctx.actor
    cs = _child_sents(rest)
    if cs:
        if hero is not None:
            ctx.actor = hero
        return coherent(ctx, hero, cs)
    emo = _vals(kw, "emotion")
    feel = _phrases(chars[1:]) + _phrases(rest) + ([state_to_phrase(emo)] if emo is not None else [])
    f = NLGUtils.join_list([x for x in feel if x])
    if hero is not None:
        ctx.actor = hero
        return f"{ctx.say(hero)} reacted with {f}." if f else f"{ctx.say(hero)} did not know how to react."
    return f"Everyone reacted with {f}." if f else "There was a big reaction."


def Knowledge(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    hero = chars[0] if chars else ctx.actor
    fact = _vals(kw, "fact")
    detail = _phrases(chars[1:]) + _phrases(rest) + ([to_phrase(fact)] if fact is not None else [])
    d = NLGUtils.join_list([x for x in detail if x])
    if hero is not None:
        ctx.actor = hero
        hero.add_meme("Wisdom", 0.3)
        return f"{ctx.say(hero)} knew about {d}." if d else f"{ctx.say(hero)} knew just what to do."
    return f"It was good to know about {d}." if d else "It was good to know."


def Continuation(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else ctx.actor
    act = _vals(kw, "activity", "action")
    sents = _child_sents(list(rest) + [act])
    if actor is not None:
        ctx.actor = actor
        lead = f"{ctx.say(actor)} carried on."
    else:
        lead = "And so it continued."
    return coherent(ctx, actor, [lead] + sents) if sents else lead


def Goal(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    hero = chars[0] if chars else ctx.actor
    role = kw.get("role")
    if hero is not None and role is not None:
        ctx.actor = hero
        r = _bare(to_phrase(role))
        return f"{ctx.say(hero)} wanted to be {NLGUtils.article(r)} {r}."
    aim = NLGUtils.join_list(_phrases(chars[1:]) + _phrases(rest))
    if hero is not None:
        ctx.actor = hero
        return f"{ctx.say(hero)}'s goal was {aim}." if aim else f"{ctx.say(hero)} had a goal in mind."
    return f"The goal was {aim}." if aim else "There was a goal to reach."


# ---------------------------------------------------------------------------
# Threats / setbacks
# ---------------------------------------------------------------------------

def Danger(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    src = NLGUtils.join_list(_phrases(rest) + _phrases([kw.get("location")] if kw.get("location") else []))
    if chars:
        chars[0].add_meme("Fear", 0.4)
        ctx.actor = chars[0]
    return f"There was danger from {src}." if src else "Danger was near."


def Crisis(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    if chars:
        chars[0].add_meme("Fear", 0.3)
        ctx.actor = chars[0]
    prob = NLGUtils.join_list(_phrases(rest) + _phrases([kw.get("problem")] if kw.get("problem") else []))
    return f"Suddenly, there was a crisis: {prob}." if prob else "Suddenly, there was a crisis."


def Disruption(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    cause = NLGUtils.join_list(_phrases(rest) + _phrases([kw.get("cause")] if kw.get("cause") else []))
    return f"Suddenly, {cause} disrupted everything." if cause else "Suddenly, everything was disrupted."


def Temptation(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    hero = chars[0] if chars else ctx.actor
    lure = NLGUtils.join_list(_phrases(chars[1:]) + _phrases(rest)
                              + _phrases([kw.get("target")] if kw.get("target") else []))
    if hero is not None:
        ctx.actor = hero
        return f"{ctx.say(hero)} was tempted by {lure}." if lure else f"{ctx.say(hero)} felt very tempted."
    return f"{_cap(lure)} was very tempting." if lure else "It was very tempting."


def Disobedience(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    hero = chars[0] if chars else ctx.actor
    sents = _child_sents(list(rest) + [kw.get("process"), kw.get("reject"), kw.get("request")])
    if hero is not None:
        ctx.actor = hero
        lead = f"{ctx.say(hero)} did not listen."
        return coherent(ctx, hero, [lead] + sents) if sents else lead
    return "There was some disobedience."


# ---------------------------------------------------------------------------
# Object-first events / states
# ---------------------------------------------------------------------------

def Missing(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    obj = _vals(kw, "object")
    thing = NLGUtils.join_list(_phrases(chars[1:]) + _phrases(rest)
                               + ([to_phrase(obj)] if obj is not None else []))
    if chars:
        ctx.actor = chars[0]
        chars[0].add_meme("Sadness", 0.3)
        return f"{chars[0]} could not find {thing}." if thing else f"{ctx.say(chars[0])} was missing."
    return f"{_cap(thing)} was missing." if thing else "Something was missing."


def New(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    thing = NLGUtils.join_list(_phrases(rest) + _phrases([kw.get("toy")] if kw.get("toy") else []))
    if thing:
        thing = _bare(thing)
        return f"There was {NLGUtils.article('new')} new {thing}."
    return "There was something new."


def Mess(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    things = NLGUtils.join_list(_phrases(rest) + _phrases([kw.get("items")] if kw.get("items") else []))
    if chars:
        ctx.actor = chars[0]
        return f"{chars[0]} made a big mess with {things}." if things else f"{chars[0]} made a big mess."
    return f"There was a big mess of {things}." if things else "There was a big mess everywhere."


def Attached(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    hero = chars[0] if chars else ctx.actor
    if hero is not None and is_meta_call(kw):
        m = meta_story(ctx, hero, kw)
        if m:
            return m
    thing = NLGUtils.join_list(_phrases(chars[1:]) + _phrases(rest))
    if hero is not None:
        ctx.actor = hero
        hero.add_meme("Love", 0.3)
        return f"{ctx.say(hero)} was very attached to {thing}." if thing else f"{ctx.say(hero)} grew very attached."
    return f"{_cap(thing)} was very special." if thing else "It was very special."


# ---------------------------------------------------------------------------
# Sensitive / life events
# ---------------------------------------------------------------------------

def Death(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    if chars:
        ctx.actor = chars[0]
        return f"Sadly, {chars[0]} passed away."
    thing = NLGUtils.join_list(_phrases(rest))
    return f"Sadly, {thing} was no more." if thing else "Sadly, it was the end."


def Injury(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    actor = chars[0] if chars else None
    part = _vals(kw, "part", "wound")
    bits = _phrases(rest) + ([to_phrase(part)] if part is not None else [])
    thing = NLGUtils.join_list(bits)
    if actor is not None:
        ctx.actor = actor
        actor.add_meme("Sadness", 0.3)
        return f"{ctx.say(actor)} hurt {thing}." if thing else f"{ctx.say(actor)} got hurt."
    if thing:
        return f"{_cap(thing)} got hurt."
    return "There was an injury."


def Flight(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    if chars:
        ctx.actor = chars[0]
        chars[0].add_meme("Joy", 0.2)
        return f"{ctx.say(chars[0])} flew up into the sky."
    thing = NLGUtils.join_list(_phrases(rest))
    return f"{_cap(thing)} took flight." if thing else "Up into the sky it flew."


def Farewell(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    if len(chars) >= 2:
        chars[0].add_meme("Sadness", 0.2)
        ctx.actor = chars[0]
        return f"{chars[0]} said goodbye to {NLGUtils.join_list([str(c) for c in chars[1:]])}."
    if chars:
        ctx.actor = chars[0]
        return f"{ctx.say(chars[0])} said goodbye."
    place = NLGUtils.join_list(_phrases(rest))
    return f"They said goodbye to {place}." if place else "And so they said their goodbyes."


def Picnic(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    hero = chars[0] if chars else ctx.actor
    loc = _vals(kw, "location")
    place = to_phrase(loc) if loc is not None else NLGUtils.join_list(_phrases(rest))
    who = NLGUtils.join_list([str(c) for c in chars]) if chars else (ctx.say(hero) if hero else "They")
    for c in chars:
        c.add_meme("Joy", 0.3)
    if hero is not None:
        ctx.actor = hero
    return f"{who} had a lovely picnic at {place}." if place else f"{who} had a lovely picnic."


def Unexpected(ctx: World, *args, **kw) -> str:
    chars, rest = _split(args)
    sents = _child_sents(rest)
    if sents:
        sents = [_lead_join("Unexpectedly, ", sents[0])] + sents[1:]
        return coherent(ctx, chars[0] if chars else None, sents)
    thing = NLGUtils.join_list(_phrases(rest))
    return f"Unexpectedly, {thing} happened." if thing else "Something unexpected happened."


def Cooperate(ctx: World, *args, **kw) -> str:
    return _Collaboration(ctx, *args, **kw)


for _name, _fn in [
    ("Go", Go), ("Sharing", Sharing), ("Shared", Sharing),
    ("Exploration", Exploration), ("Creation", Creation), ("Home", Home),
    ("Illness", Illness), ("Choice", Choice), ("Task", Task),
    ("Reaction", Reaction), ("Knowledge", Knowledge),
    ("Continuation", Continuation), ("Goal", Goal), ("Danger", Danger),
    ("Crisis", Crisis), ("Disruption", Disruption), ("Temptation", Temptation),
    ("Disobedience", Disobedience), ("Missing", Missing), ("New", New),
    ("Mess", Mess), ("Attached", Attached), ("Attachment", Attached),
    ("Death", Death), ("Injury", Injury), ("Flight", Flight),
    ("Farewell", Farewell), ("Picnic", Picnic), ("Unexpected", Unexpected),
    ("Cooperate", Cooperate),
]:
    _register(_name, _fn)


if __name__ == "__main__":
    import gen6registry  # noqa: F401  (load sibling packs)
    from gen6 import generate

    tests = [
        "Lily(Character, girl)\nReach(bowl)\nGrab(Lily, cookie)\nPaint(tree)",
        "Tim(Character, boy)\nDad(Character, father)\nSwim(Tim, Dad, water)\nGo(Tim, park)",
        "Lily(Character, girl)\nMom(Character, mother)\nThanks(Lily, Mom)\nSharing(Lily, Mom, cake)\nBonding(Lily, Mom)",
        "Sam(Character, boy)\nInjury(Sam, head)\nIllness(Sam)\nHeal(Sam)",
        "Lily(Character, girl)\nExploration(Lily, process=Find(shell) + See(fish), outcome=Joy)\nCreation(Lily)\nMissing(ball)",
        "Anna(Character, girl)\nBen(Character, boy)\nPicnic(Anna, Ben, location=park)\nFarewell(Anna, Ben)\nDeath(Lion)",
        "Lily(Character, girl)\nNew(carSeat)\nBroken(toy)\nMess(room, blocks)\nDanger(spider)",
    ]
    for i, t in enumerate(tests, 1):
        print(f"--- TEST {i} ---")
        print(generate(t))
        print()
