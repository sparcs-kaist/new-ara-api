from unittest.mock import call, patch

from django.contrib.admin.sites import AdminSite
from django.test import SimpleTestCase, TestCase

from apps.course.admin import CourseGroupingRuleAdmin
from apps.course.grouping import (
    COURSE_CODE_GROUP_KEY,
    grouping_key_for,
    regroup_existing_courses,
)
from apps.course.models import Course, CourseGroup, CourseGroupingRule


class CourseGroupingKeyTest(SimpleTestCase):
    def test_default_strategy_keeps_professors_key(self):
        self.assertEqual(grouping_key_for("10,20"), "10,20")
        self.assertEqual(
            grouping_key_for(
                "10,20",
                CourseGroupingRule.Strategy.CODE_AND_PROFESSORS,
            ),
            "10,20",
        )

    def test_course_code_strategy_uses_shared_key(self):
        self.assertEqual(
            grouping_key_for(
                "10,20",
                CourseGroupingRule.Strategy.COURSE_CODE,
            ),
            COURSE_CODE_GROUP_KEY,
        )


class RegroupExistingCoursesTest(TestCase):
    def setUp(self):
        self.group_a = CourseGroup.objects.create(
            course_code="MAS101",
            professors_key="10",
            title="미적분학 I",
            title_year=2025,
            title_semester=1,
        )
        self.group_b = CourseGroup.objects.create(
            course_code="MAS101",
            professors_key="20",
            title="미적분학 I",
            title_year=2026,
            title_semester=1,
        )
        self.course_a = Course.objects.create(
            course_code="MAS101",
            title="미적분학 I",
            year=2025,
            semester=1,
            group=self.group_a,
            professors_key="10",
            otl_course_id=1,
            otl_lecture_ids=[101],
        )
        self.course_b = Course.objects.create(
            course_code="MAS101",
            title="미적분학 I",
            year=2026,
            semester=1,
            group=self.group_b,
            professors_key="20",
            otl_course_id=1,
            otl_lecture_ids=[201],
        )

    def test_course_code_rule_merges_existing_course_groups(self):
        CourseGroupingRule.objects.create(
            course_code="mas101",
            strategy=CourseGroupingRule.Strategy.COURSE_CODE,
        )

        regroup_existing_courses("MAS101")

        self.course_a.refresh_from_db()
        self.course_b.refresh_from_db()
        self.assertEqual(self.course_a.group_id, self.course_b.group_id)
        self.assertEqual(
            self.course_a.group.professors_key,
            COURSE_CODE_GROUP_KEY,
        )

    def test_disabling_rule_restores_professor_groups(self):
        rule = CourseGroupingRule.objects.create(
            course_code="MAS101",
            strategy=CourseGroupingRule.Strategy.COURSE_CODE,
        )
        regroup_existing_courses(rule.course_code)
        self.course_a.refresh_from_db()
        self.course_b.refresh_from_db()
        self.assertEqual(self.course_a.group_id, self.course_b.group_id)

        rule.is_active = False
        rule.save(update_fields=["is_active", "updated_at"])
        regroup_existing_courses(rule.course_code)

        self.course_a.refresh_from_db()
        self.course_b.refresh_from_db()
        self.assertNotEqual(self.course_a.group_id, self.course_b.group_id)
        self.assertEqual(self.course_a.group.professors_key, "10")
        self.assertEqual(self.course_b.group.professors_key, "20")


class CourseGroupingRuleAdminTest(TestCase):
    def test_changing_course_code_regroups_old_and_new_codes(self):
        rule = CourseGroupingRule.objects.create(
            course_code="MAS101",
            strategy=CourseGroupingRule.Strategy.COURSE_CODE,
        )
        rule.course_code = "EE209"
        model_admin = CourseGroupingRuleAdmin(CourseGroupingRule, AdminSite())

        with patch("apps.course.admin.regroup_existing_courses") as regroup:
            model_admin.save_model(None, rule, None, change=True)

        self.assertEqual(
            regroup.call_args_list,
            [call("MAS101"), call("EE209")],
        )
