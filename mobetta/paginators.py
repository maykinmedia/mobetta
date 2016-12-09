from django.core.paginator import Paginator


class MovingRangePaginator(Paginator):

    def limited_range(self, current_page_number):
        """ Return a moving range of 10 pages."""
        current_page_number = current_page_number or 1

        high_bound = min(
            max(current_page_number + 5, 10),
            self.num_pages
        ) + 1

        return range(
            max(high_bound - 10, 1),
            high_bound
        )
