"""Standalone script to generate word vocabularies from monolingual corpus."""

import argparse

from opennmt import constants
from opennmt import tokenizers
from opennmt import data


def main():
  parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument(
      "data", nargs="*",
      help="Source text file.")
  parser.add_argument(
      "--from_vocab", default=None,
      help="Build from a saved vocabulary (see also --from_format).")
  parser.add_argument(
      "--from_format", default="default", choices=["default", "sentencepiece"],
      help="The format of the saved vocabulary (see also --from_vocab).")
  parser.add_argument(
      "--save_vocab", required=True,
      help="Output vocabulary file.")
  parser.add_argument(
      "--min_frequency", type=int, default=1,
      help="Minimum word frequency.")
  parser.add_argument(
      "--size", type=int, default=0,
      help="Maximum vocabulary size. If = 0, do not limit vocabulary.")
  parser.add_argument(
      "--size_multiple", type=int, default=1,
      help=("Ensure that the vocabulary size + 1 is a multiple of this value "
            "(+ 1 represents the <unk> token that will be added during the training."))
  parser.add_argument(
      "--without_sequence_tokens", default=False, action="store_true",
      help="If set, do not add special sequence tokens (start, end) in the vocabulary.")
  parser.add_argument(
      "--tokenizer_config", default=None,
      help="Tokenization configuration.")
  parser.add_argument(
      "--sentencepiece", nargs="*", default=None,
      help=("Build a SentencePiece model and vocabulary. This option accepts additional "
            "training parameters (e.g. --sentencepiece character_coverage=0.98)."))
  args = parser.parse_args()

  special_tokens = [constants.PADDING_TOKEN]
  if not args.without_sequence_tokens:
    special_tokens.append(constants.START_OF_SENTENCE_TOKEN)
    special_tokens.append(constants.END_OF_SENTENCE_TOKEN)

  vocab = data.Vocab(special_tokens=special_tokens)
  num_oov_buckets = 1

  if args.sentencepiece is not None:
    import pyonmttok
    if args.size_multiple == 1:
      vocab_size = args.size
    else:
      # Round vocabulary size to the next multiple of args.size_multiple
      vocab_size = (
          args.size - (args.size + num_oov_buckets) % args.size_multiple + args.size_multiple)
    sp_params = dict(map(lambda arg: tuple(arg.split("=")), args.sentencepiece))
    sp_trainer = pyonmttok.SentencePieceLearner(
        keep_vocab=True, vocab_size=vocab_size, **sp_params)
    for data_file in args.data:
      sp_trainer.ingest_file(data_file)
    sp_trainer.learn(args.save_vocab, verbose=True)
    args.save_vocab = args.save_vocab + ".vocab"
    vocab.load(args.save_vocab, file_format="sentencepiece")
  else:
    if args.from_vocab is not None:
      vocab.load(args.from_vocab, file_format=args.from_format)
    tokenizer = tokenizers.make_tokenizer(args.tokenizer_config)
    for data_file in args.data:
      vocab.add_from_text(data_file, tokenizer=tokenizer)
    vocab = vocab.prune(max_size=args.size, min_frequency=args.min_frequency)
    vocab.pad_to_multiple(args.size_multiple, num_oov_buckets=num_oov_buckets)

  vocab.serialize(args.save_vocab)


if __name__ == "__main__":
  main()
