#include <QApplication>
#include <QMainWindow>
#include <QTextEdit>
#include <QFile>
#include <QTextStream>
#include <QVBoxLayout>
#include <QWidget>
#include <QLabel>
#include <QMap>
#include <QMessageBox>
#include <qdebug.h>
#include <yaml-cpp/yaml.h>
#include <QInputDialog>
#include <QPushButton>

class PackageInfoWidget : public QWidget {
public:
    PackageInfoWidget(QWidget *parent = nullptr) : QWidget(parent) {
        QVBoxLayout *layout = new QVBoxLayout(this);

        QLabel *title = new QLabel("Package Information", this);
        layout->addWidget(title);

        QTextEdit *textEdit = new QTextEdit(this);
        textEdit->setReadOnly(true);
        layout->addWidget(textEdit);

        QPushButton *button = new QPushButton("Select Package", this);
        layout->addWidget(button);

        connect(button, &QPushButton::clicked, this, &PackageInfoWidget::showPackageSelection);

        if (loadPackageInfo()) {
            textEdit->setText(packageInfoText);
        } else {
            textEdit->setText("Failed to load package information.");
        }
    }

private:
    QString packageInfoText;
    QList<QString> packageNames;

    bool loadPackageInfo() {
        QFile file("../../packages.yaml");
        if (!file.open(QIODevice::ReadOnly | QIODevice::Text)) {
            QMessageBox::critical(this, "Error", "Could not open file for reading.");
            return false;
        }

        QTextStream in(&file);
        QString content = in.readAll();
        file.close();

        try {
            YAML::Node doc = YAML::Load(content.toStdString());

            for (const auto &node : doc) {
                const YAML::Node &pkg = node.second;
                packageInfoText += QString("Name: %1\n").arg(QString::fromStdString(pkg["name"].as<std::string>()));
                packageInfoText += QString("Description: %1\n").arg(QString::fromStdString(pkg["des"].as<std::string>()));
                packageInfoText += QString("URL: %1\n").arg(QString::fromStdString(pkg["url"].as<std::string>()));
                packageInfoText += QString("Version: %1\n\n").arg(QString::fromStdString(pkg["version"].as<std::string>()));

                packageNames.append(QString::fromStdString(pkg["name"].as<std::string>()));
            }
        } catch (const YAML::Exception &e) {
            QMessageBox::critical(this, "Error", QString::fromStdString(e.what()));
            return false;
        }

        return true;
    }

    void showPackageSelection() {
        bool ok;
        QString selectedPackage = QInputDialog::getItem(this, "Select Package", "Choose a package:", packageNames, 0, false, &ok);

        if (ok && !selectedPackage.isEmpty()) {
            QPushButton *button = qobject_cast<QPushButton*>(sender());
            button->setText(selectedPackage);
        }
    }
};

int main(int argc, char *argv[]){
    QApplication app(argc, argv);
    // QMainWindow window;
    // qDebug() << "win is hidden: "<< window.isHidden();
    // window.show();

    PackageInfoWidget widget;
    widget.show();

    return app.exec();
}