
def get_spacy_nlp_pipeline_for_indian_legal_text(model_name="en_core_web_sm", disable=['ner'], punc=[".", "?", "!"],custom_ner = False):
    ########## Creates spacy nlp pipeline for indian legal text. the sentence splitting is done on specific punctuation marks.
    #########This is finalized after multiple experiments comparison. To use all components pass empty list  disable = []

    import spacy
    from spacy.pipeline import Sentencizer

    nlp = spacy.load(model_name, disable=disable)
    nlp.max_length = 30000000

    ############ special tokens which should not be split in tokenization.
    #           this is specially helpful when we use models which split on the dots present in these abbreviations
    # special_tokens_patterns_list = [r'nos?\.',r'v\/?s\.?',r'rs\.',r'sh?ri\.']
    # special_tokens = re.compile( '|'.join(special_tokens_patterns_list),re.IGNORECASE).match
    # nlp.tokenizer = Tokenizer(nlp.vocab,token_match = special_tokens)

    ############## Custom NER patterns
    patterns = [{"label": "RESPONDENT",
                 "pattern": [{"LOWER": "respondent"},
                             {"TEXT": {"REGEX": "(^(?i)numbers$)|(^(?i)number$)|(^(?i)nos\.\d+$)|(^(?i)no\.\d+$)"}},
                             {"TEXT": {"REGEX": "(\d+|\,|and|to)"}, "OP": "+"},
                             {"TEXT": {"REGEX": "\d+"}}]},
                {"label": "RESPONDENT",
                 "pattern": [{"LOWER": "respondent"},
                             {"TEXT": {"REGEX": "(^(?i)numbers$)|(^(?i)number$)|(^(?i)nos\.\d+$)|(^(?i)no\.\d+$)"}},
                             {"TEXT": {"REGEX": "(^(?i)no\.\d+$)"}, "OP": "*"},
                             {"TEXT": {"REGEX": "(\d+)"}, "OP": "*"}]},
                {"label": "WITNESS",
                 "pattern": [{"TEXT": {"REGEX": r"^(?i)PW\-\d*\w+$"}},
                             {"TEXT": {"REGEX": r"^(\/|[A-Z])$"}, "OP": "*"}]},
                {"label": "WITNESS",
                 "pattern": [{"LOWER": "prosecution"}, {"TEXT": {"REGEX": r"(^(?i)Witness\-\S+$)|(^(?i)witness)"}},
                             {"TEXT": {"REGEX": "(\d+)"}, "OP": "*"},
                             {"TEXT": {"REGEX": r"^(\/|[A-Z])$"}, "OP": "*"}]},
                {"label": "WITNESS",
                 "pattern": [{"TEXT": {"REGEX": "(^(?i)PW$)"}}, {"TEXT": {"REGEX": "(\d+)"}},
                             {"TEXT": {"REGEX": r"^(\/|[A-Z])$"}, "OP": "*"}]},
                {"label": "ACCUSED",
                 "pattern": [{"LOWER": "accused"},
                             {"TEXT": {"REGEX": "(^(?i)numbers$)|(^(?i)number$)|(^(?i)nos\.\d+$)|(^(?i)no\.\d+$)"}},
                             {"TEXT": {"REGEX": "(\d+|\,|and|to)"}, "OP": "+"},
                             {"TEXT": {"REGEX": "\d+"}}]},
                {"label": "ACCUSED",
                 "pattern": [{"LOWER": "accused"},
                             {"TEXT": {"REGEX": "(^(?i)numbers$)|(^(?i)number$)|(^(?i)nos\.\d+$)|(^(?i)no\.\d+$)"}},
                             {"TEXT": {"REGEX": "(^(?i)no\.\d+$)"}, "OP": "*"},
                             {"TEXT": {"REGEX": "(\d+)"}, "OP": "*"}]}]


    if int(spacy.__version__.split(".")[0]) >= 3:
        ########### For transformer model use built in sentence splitting. For others, use sentence splitting on punctuations.
        ########### This is because transformer sentence spiltting is doing better than the punctuation spiltting
        if model_name!="en_core_web_trf":
            config = {"punct_chars": punc}
            nlp.add_pipe("sentencizer", config=config, before='parser')

        if "ner" not in disable and custom_ner:
            ruler = nlp.add_pipe("entity_ruler", before='ner')
            ruler.add_patterns(patterns)

    else:
        if model_name != "en_core_web_trf":
            sentencizer = Sentencizer(punct_chars=punc)
            nlp.add_pipe(sentencizer, before="parser")
        if "ner" not in disable and custom_ner:
            from spacy.pipeline import EntityRuler
            ruler = EntityRuler(nlp, overwrite_ents=True)
            ruler.add_patterns(patterns)
            nlp.add_pipe(ruler, before='ner')

    return nlp



def attach_short_sentence_boundries_to_next(revised_sentence_boundries, doc_txt):
    ###### this function accepts the list in the format of output of function "extract_relevant_sentences_for_rhetorical_roles" and returns the revised list with shorter sentences attached to next sentence
    min_char_cnt_per_sentence = 5

    concatenated_sentence_boundries = []
    sentences_to_attach_to_next = ()
    for sentence_boundry in revised_sentence_boundries:
        sentence_txt = doc_txt[sentence_boundry[0]: sentence_boundry[1]]
        if not sentence_txt.isspace():  ### sentences containing only spaces , newlines are discarded
            if sentences_to_attach_to_next:
                sentence_start_char = sentences_to_attach_to_next[0]
            else:
                sentence_start_char = sentence_boundry[0]
            sentence_length_char = sentence_boundry[1] - sentence_start_char
            if sentence_length_char > min_char_cnt_per_sentence:
                concatenated_sentence_boundries.append((sentence_start_char,sentence_boundry[1]))
                sentences_to_attach_to_next = ()
            else:
                if not sentences_to_attach_to_next:
                    sentences_to_attach_to_next = sentence_boundry
    return concatenated_sentence_boundries
