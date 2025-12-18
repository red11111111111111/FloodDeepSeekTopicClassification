import torch
import pickle as pkl  # 新增导入


class Config:
    def __init__(self):
        self.dataset = 'THUCNews'
        self.model_name = 'TextCNN'
        self.vocab_path = 'model/vocab.pkl'
        self.save_path = 'model/TextCNN.ckpt'
        self.class_list = ['finance', 'realty', 'stocks', 'education', 'science',
                           'society', 'politics', 'sports', 'game', 'entertainment']
        self.pad_size = 32
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')  # 自动检测GPU

        # 新增参数
        self.embedding_pretrained = None
        self.n_vocab = len(pkl.load(open(self.vocab_path, 'rb')))
        self.embed = 300
        self.filter_sizes = (2, 3, 4)
        self.num_filters = 256
        self.dropout = 0.4
        self.num_classes = len(self.class_list)
