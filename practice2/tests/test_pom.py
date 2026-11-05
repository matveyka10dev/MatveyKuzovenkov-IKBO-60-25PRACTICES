"""Тесты разбора XML-файлов Maven."""

import unittest

from depviz.pom import PomError, parse_latest_version, parse_pom

SOURCE = "test.pom"
NAMESPACED_POM = b"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <parent>
    <groupId>org.example</groupId>
    <artifactId>parent</artifactId>
    <version>1.0</version>
  </parent>
  <artifactId>child</artifactId>
  <properties>
    <lib.version>2.0</lib.version>
  </properties>
  <dependencyManagement>
    <dependencies>
      <dependency>
        <groupId>g</groupId>
        <artifactId>managed</artifactId>
        <version>3.0</version>
      </dependency>
    </dependencies>
  </dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>g</groupId>
      <artifactId>lib</artifactId>
      <version>${lib.version}</version>
      <scope>test</scope>
      <optional>true</optional>
    </dependency>
  </dependencies>
  <build>
    <plugins>
      <plugin>
        <artifactId>p</artifactId>
        <dependencies>
          <dependency>
            <groupId>g</groupId>
            <artifactId>plugin-only</artifactId>
          </dependency>
        </dependencies>
      </plugin>
    </plugins>
  </build>
</project>
"""


def metadata(versioning):
    """Сформировать maven-metadata.xml с заданным разделом versioning.

    :param versioning: XML внутри элемента versioning.
    :return: содержимое файла (bytes).
    """
    return ("<metadata><versioning>{}</versioning></metadata>"
            .format(versioning).encode("utf-8"))


class ParsePomTest(unittest.TestCase):
    """Проверка parse_pom."""

    def setUp(self):
        """Разобрать пример POM с пространством имён."""
        self.pom = parse_pom(NAMESPACED_POM, SOURCE)

    def test_inherited_coordinate(self):
        """groupId и version наследуются от parent."""
        self.assertEqual(str(self.pom.coordinate), "org.example:child:1.0")
        self.assertEqual(str(self.pom.parent), "org.example:parent:1.0")

    def test_properties(self):
        """Свойства читаются без подстановки."""
        self.assertEqual(self.pom.properties, {"lib.version": "2.0"})

    def test_dependencies(self):
        """Зависимости плагинов не учитываются."""
        self.assertEqual(len(self.pom.dependencies), 1)
        dependency = self.pom.dependencies[0]
        self.assertEqual(str(dependency.coordinate), "g:lib:${lib.version}")
        self.assertEqual(dependency.scope, "test")
        self.assertTrue(dependency.optional)

    def test_managed(self):
        """Раздел dependencyManagement читается отдельно."""
        self.assertEqual([str(item.coordinate) for item in self.pom.managed],
                         ["g:managed:3.0"])

    def test_without_namespace(self):
        """POM без пространства имён тоже разбирается."""
        pom = parse_pom(b"<project><groupId>g</groupId>"
                        b"<artifactId>a</artifactId><version>1</version>"
                        b"</project>", SOURCE)
        self.assertEqual(str(pom.coordinate), "g:a:1")
        self.assertEqual(pom.dependencies, [])

    def test_errors(self):
        """Неверный XML, чужой корень, нет artifactId - ошибки."""
        cases = [
            (b"<project>", "invalid XML"),
            (b"<html/>", "expected <project>"),
            (b"<project><groupId>g</groupId></project>", "artifactId"),
            (b"<project><artifactId>a</artifactId><dependencies>"
             b"<dependency><artifactId>x</artifactId></dependency>"
             b"</dependencies></project>", "without groupId"),
        ]
        for data, message in cases:
            with self.subTest(data=data):
                with self.assertRaisesRegex(PomError, message):
                    parse_pom(data, SOURCE)


class ParseLatestVersionTest(unittest.TestCase):
    """Проверка parse_latest_version."""

    def test_release(self):
        """В первую очередь берётся release."""
        data = metadata("<latest>2.0-SNAPSHOT</latest><release>1.0</release>")
        self.assertEqual(parse_latest_version(data, SOURCE), "1.0")

    def test_latest(self):
        """Без release берётся latest."""
        data = metadata("<latest>2.0</latest>")
        self.assertEqual(parse_latest_version(data, SOURCE), "2.0")

    def test_last_version(self):
        """Без release и latest - последняя версия из списка."""
        data = metadata("<versions><version>1</version>"
                        "<version>3</version></versions>")
        self.assertEqual(parse_latest_version(data, SOURCE), "3")

    def test_no_versions(self):
        """Нет версий или неверный корень - ошибка."""
        for data in (metadata("<versions/>"), b"<project/>"):
            with self.subTest(data=data):
                with self.assertRaises(PomError):
                    parse_latest_version(data, SOURCE)


if __name__ == "__main__":
    unittest.main()
