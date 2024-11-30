#pragma once

#include <QWidget>
#include <QComboBox>
#include <QStringList>
#include <QVBoxLayout>

class SelectionWidget : public QWidget {
    // Q_OBJECT

public:
    explicit SelectionWidget(QWidget *parent = nullptr) : QWidget(parent), comboBox(new QComboBox(this)) {
        QVBoxLayout *layout = new QVBoxLayout(this);
        layout->addWidget(comboBox);
        setLayout(layout);

        // 连接 QComboBox 的 currentIndexChanged 信号到自定义的槽函数
        connect(comboBox, QOverload<int>::of(&QComboBox::currentIndexChanged), this, &SelectionWidget::onOptionChanged);
    }

    void setOptions(const QStringList &options) {
        comboBox->clear();
        comboBox->addItems(options);
    }

    QString getSelectedOption() const {
        return comboBox->currentText();
    }
// signals:
//     void optionChanged(const QString &option);

private slots:
    void onOptionChanged(int index) {
        QString selectedOption = comboBox->itemText(index);
        qDebug() << "Selected option:" << selectedOption;
        // emit optionChanged(selectedOption);
    }
private:
    QComboBox *comboBox;
};