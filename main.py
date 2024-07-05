from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QApplication, QMainWindow, QMessageBox)
from mainui import Ui_MainWindow
from sklearn.tree import DecisionTreeClassifier
from gensim.models import Word2Vec
import sys, re, pickle, os
import pandas as pd
import numpy as np

class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.font = QFont()
        self.font.setPointSize(11)
        self.ui.description_ip.setFont(self.font)
        self.ui.find_btn.clicked.connect(self.find_genre)
        self.ui.clear_btn.clicked.connect(self.clear)

        train_data_loc = os.path.join("movie-data", "train_data.txt")

        train_data = pd.read_csv(train_data_loc, delimiter=" ::: ", header=None, names=["id", "title", "genre", "description"], encoding="utf-8", engine="python")
        
        train_data["description"] = train_data["description"].apply(self.clean_data)
         
        x_train = train_data["description"] #this is like a question
        y_train = train_data["genre"] #this is like an answer

        sumlist = []
        for summary in x_train:
            sumlist.append(summary.split())

        w2v_model_path = os.path.join("model", "w2v_model.model")
        if os.path.isfile(w2v_model_path):
            self.w2v_model = Word2Vec.load(w2v_model_path)
        else:
            self.w2v_model = Word2Vec(sumlist, window=50, min_count=5, workers=12, epochs=10)
            self.w2v_model.save(w2v_model_path)
        l = []
        for summary in x_train:
            l.append(self.vectorize(summary))
        x_train = np.array(l)

        m_path = os.path.join("model", "model.pkl")
        if os.path.isfile(m_path):
            with open(m_path, 'rb') as f:
                self.model = pickle.load(f)
        else:
            self.model = DecisionTreeClassifier(max_features=self.w2v_model.vector_size)
            self.model.fit(x_train, y_train)
            with open(m_path, 'wb') as f:
                pickle.dump(self.model, f)


    def vectorize(self, text):
        words = text.split()
        l = []
        for word in words:
            if word in self.w2v_model.wv:
                l.append(self.w2v_model.wv[word])
        words_vecs = l
        if len(words_vecs) == 0:
            return np.zeros(self.w2v_model.vector_size)
        words_vecs = np.array(words_vecs)
        return words_vecs.mean(axis=0)


    def find_genre(self):
        textip = self.ui.description_ip.toPlainText()
        cleaned_text = self.clean_data(textip)
        x_input = self.vectorize(cleaned_text).reshape(1, -1)
        predict = self.model.predict(x_input)
        if predict != "":
            QMessageBox.information(self, "Genre finder", f"According to the description provided, the genre of the movie is {predict[0]}")


    def clean_data(self, txt):
        txt = txt.lower()
        txt = re.sub(r'[^\w\s]', "", txt)
        return txt


    def clear(self):
        self.ui.description_ip.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()
    sys.exit(app.exec())