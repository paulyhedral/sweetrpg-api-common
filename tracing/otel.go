package tracing

import (
	"context"
	"fmt"
	"strings"

	options "go.jtlabs.io/query"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	oteltrace "go.opentelemetry.io/otel/trace"
)

func BuildSpanWithOptions(c context.Context, tracerName string, spanName string, options options.Options) oteltrace.Span {

	pageItems := make([]string, len(options.Page))
	for k, v := range options.Page {
		pageItems = append(pageItems, fmt.Sprintf("%s=%d", k, v))
	}

	filterItems := make([]string, len(options.Filter))
	for k, v := range options.Filter {
		filterItems = append(filterItems, fmt.Sprintf("%s=%s", k, strings.Join(v, ",")))
	}

	_, span := otel.Tracer(tracerName).Start(c, spanName,
		oteltrace.WithAttributes(attribute.StringSlice("fields", options.Fields)),
		oteltrace.WithAttributes(attribute.StringSlice("sort", options.Sort)),
		oteltrace.WithAttributes(attribute.StringSlice("filter", filterItems)),
		oteltrace.WithAttributes(attribute.StringSlice("page", pageItems)))

	return span
}
