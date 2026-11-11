"""Five latents -> two 16-head layers -> joint attributed vocabulary grammars."""

import argparse
import json

from .grammar import Gap, GrammarNeuron, Lookup, Present, Ref, Rule, Seq, Token
from .transformer import GrammarHead, GrammarProjection, Storyformer, StoryformerBlock


def make_demo():
    # Copy an actor from anywhere in the visible prefix onto the current verb.
    acquisition = Seq(Token(bind="actor", entity=Present()), Gap(), Token(token="took"))
    copy = GrammarHead(GrammarNeuron("copy_actor", (
        Rule(acquisition, {"actor": Ref("actor.token")}),)))
    # This head needs copy_actor's output, so it first activates in layer two.
    lookup = GrammarHead(GrammarNeuron("predicate_event", (
        Rule(Seq(Gap(), Token(actor=Present(), token="took")),
             {"event": Lookup("events", Ref("query.token"))}),),
        tables={"events": {"took": "obtain tool"}}))
    layers = [StoryformerBlock((copy, lookup)) for _ in range(2)]
    neurons = {}
    for word, weight in (("scissors", 6.), ("needle", 3.), ("thread", 1.)):
        nouns = {"pos": "n", "entity": word}
        neurons[word] = GrammarNeuron("next_" + word, (
            Rule(Seq(Gap(), Token(event="obtain tool", actor=Present())),
                 {**nouns, "role": "patient", "location": Ref("query.actor"), "event": Ref("query.event")}, weight),
            Rule(Seq(Gap(), Token(token="took")), nouns, .1),
        ))
    neurons["<END>"] = GrammarNeuron("end_after_object", (
        Rule(Seq(Gap(), Token(pos="n")), {"pos": "end"}),))
    context = [dict(token="Lily", pos="n", entity="girl"), dict(token="needed", pos="v"),
               dict(token="tools", pos="n", entity="tools"), dict(token="and", pos="conj"),
               dict(token="took", pos="v")]
    return Storyformer(GrammarProjection(neurons), layers=layers), context


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--save", help="save a reusable grammar checkpoint")
    parser.add_argument("--trace", action="store_true")
    args = parser.parse_args()
    model, context = make_demo()
    result = model.forward(context)
    output = dict(context=context, layers=len(model.layers), heads_per_layer=[len(layer.heads) for layer in model.layers],
                  residual_stream=result.residual_stream, next_latent=result.next_latent.to_dict(),
                  generated=model.generate(context, 2, seed=7)[len(context):])
    if args.trace:
        output["trace"] = result.trace
    if args.save:
        model.save(args.save)
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
